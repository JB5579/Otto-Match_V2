"""
Conversation Export Service for Otto.AI
Generates PDF and JSON exports of conversation history for data portability and GDPR compliance.
Supports individual conversation exports and full GDPR data exports.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import io

from src.services.supabase_client import get_supabase_client
from src.memory.zep_client import ZepClient, Message

# Try to import PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.lib.colors import HexColor
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("ReportLab not installed. PDF exports will use fallback (JSON only).")

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of conversation export operation"""
    export_id: str
    export_type: str  # 'pdf', 'json', 'full_gdpr'
    file_path: Optional[str] = None  # Path to generated file
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None  # URL for download
    expires_at: Optional[datetime] = None
    created_at: datetime = None
    conversation_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ConversationExportData:
    """Structured data for conversation export"""
    conversation_id: str
    session_id: str
    user_id: Optional[str]
    title: str
    summary: str
    started_at: datetime
    ended_at: datetime
    message_count: int

    # Preferences
    preferences: Dict[str, Any]

    # Vehicles discussed
    vehicles_discussed: List[Dict[str, Any]]

    # Journey tracking
    journey_stage: str
    evolution_detected: bool

    # Messages
    messages: List[Dict[str, Any]]


class ConversationExportService:
    """Service for exporting conversation history in various formats"""

    def __init__(
        self,
        storage_path: str = "exports/conversations",
        supabase_client=None,
        zep_client: Optional[ZepClient] = None
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.supabase_client = supabase_client or get_supabase_client()
        self.zep_client = zep_client

        # Check PDF availability
        self.pdf_available = PDF_AVAILABLE
        if not self.pdf_available:
            logger.warning("PDF generation not available. Install ReportLab: pip install reportlab")

    async def export_conversation_json(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ExportResult:
        """Export a single conversation as JSON

        AC5: Export Conversation History - JSON file for data portability
        """
        try:
            logger.info(f"Exporting conversation {conversation_id} as JSON")

            # Fetch conversation data
            export_data = await self._get_conversation_export_data(
                conversation_id, user_id, session_id
            )

            # Generate JSON
            json_data = {
                "export_metadata": {
                    "export_type": "conversation_json",
                    "conversation_id": conversation_id,
                    "exported_at": datetime.now().isoformat(),
                    "format_version": "1.0"
                },
                "conversation": asdict(export_data)
            }

            # Save to file
            filename = f"conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = self.storage_path / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, default=str)

            file_size = file_path.stat().st_size

            # Record export in database
            export_record = await self._create_export_record(
                export_type="json",
                conversation_ids=[conversation_id],
                user_id=user_id,
                session_id=session_id,
                file_path=str(file_path),
                file_size_bytes=file_size
            )

            logger.info(f"JSON export complete: {file_path}")

            return ExportResult(
                export_id=export_record.get('id', ''),
                export_type="json",
                file_path=str(file_path),
                file_size_bytes=file_size,
                download_url=f"/api/v1/conversations/export/{export_record.get('id', '')}",
                expires_at=datetime.now() + timedelta(days=30),
                created_at=datetime.now(),
                conversation_count=1
            )

        except Exception as e:
            logger.error(f"Failed to export conversation as JSON: {e}")
            raise

    async def export_conversation_pdf(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ExportResult:
        """Export a single conversation as PDF

        AC5: Export Conversation History - PDF document with formatted dialogue
        """
        try:
            logger.info(f"Exporting conversation {conversation_id} as PDF")

            if not self.pdf_available:
                # Fallback to JSON if PDF not available
                logger.warning("PDF generation not available, falling back to JSON")
                return await self.export_conversation_json(conversation_id, user_id, session_id)

            # Fetch conversation data
            export_data = await self._get_conversation_export_data(
                conversation_id, user_id, session_id
            )

            # Generate PDF
            filename = f"conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = self.storage_path / filename

            await self._generate_conversation_pdf(export_data, file_path)

            file_size = file_path.stat().st_size

            # Record export in database
            export_record = await self._create_export_record(
                export_type="pdf",
                conversation_ids=[conversation_id],
                user_id=user_id,
                session_id=session_id,
                file_path=str(file_path),
                file_size_bytes=file_size
            )

            logger.info(f"PDF export complete: {file_path}")

            return ExportResult(
                export_id=export_record.get('id', ''),
                export_type="pdf",
                file_path=str(file_path),
                file_size_bytes=file_size,
                download_url=f"/api/v1/conversations/export/{export_record.get('id', '')}",
                expires_at=datetime.now() + timedelta(days=30),
                created_at=datetime.now(),
                conversation_count=1
            )

        except Exception as e:
            logger.error(f"Failed to export conversation as PDF: {e}")
            raise

    async def export_full_gdpr_data(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ExportResult:
        """Export all user data for GDPR compliance

        AC5: Request full data export (GDPR compliance)
        AC6: GDPR data export endpoint
        """
        try:
            logger.info(f"Exporting full GDPR data for user_id={user_id}, session_id={session_id}")

            # Fetch all conversations
            conversations_data = await self._get_all_conversations_for_user(user_id, session_id)

            # Compile comprehensive GDPR export
            gdpr_data = {
                "export_metadata": {
                    "export_type": "full_gdpr_export",
                    "gdpr_request": True,
                    "exported_at": datetime.now().isoformat(),
                    "format_version": "1.0"
                },
                "user_identity": {
                    "user_id": user_id,  # May be None for guest users
                    "session_id": session_id
                },
                "conversations": [asdict(conv) for conv in conversations_data],
                "aggregate_statistics": {
                    "total_conversations": len(conversations_data),
                    "total_messages": sum(c.message_count for c in conversations_data),
                    "date_range": {
                        "first_conversation": min((c.started_at for c in conversations_data), default=None),
                        "last_conversation": max((c.ended_at for c in conversations_data), default=None)
                    } if conversations_data else None
                },
                "preferences_summary": await self._compile_preferences_summary(conversations_data),
                "vehicles_discussed": await self._compile_all_vehicles(conversations_data)
            }

            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            identifier = user_id if user_id else session_id
            filename = f"gdpr_export_{identifier}_{timestamp}.json"
            file_path = self.storage_path / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(gdpr_data, f, indent=2, default=str)

            file_size = file_path.stat().st_size

            # Record export in database
            export_record = await self._create_export_record(
                export_type="full_gdpr",
                conversation_ids=[],  # All conversations
                user_id=user_id,
                session_id=session_id,
                file_path=str(file_path),
                file_size_bytes=file_size
            )

            logger.info(f"GDPR export complete: {file_path}")

            return ExportResult(
                export_id=export_record.get('id', ''),
                export_type="full_gdpr",
                file_path=str(file_path),
                file_size_bytes=file_size,
                download_url=f"/api/v1/conversations/export/{export_record.get('id', '')}",
                expires_at=datetime.now() + timedelta(days=30),
                created_at=datetime.now(),
                conversation_count=len(conversations_data)
            )

        except Exception as e:
            logger.error(f"Failed to export GDPR data: {e}")
            raise

    async def _get_conversation_export_data(
        self,
        conversation_id: str,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> ConversationExportData:
        """Fetch complete conversation data for export"""
        # Get conversation from database
        query = self.supabase_client.table('conversation_history').select('*').eq('id', conversation_id)

        if user_id:
            query = query.eq('user_id', user_id)
        else:
            query = query.is_('user_id', 'null').eq('session_id', session_id)

        result = query.execute()

        if not result.data:
            raise ValueError(f"Conversation {conversation_id} not found")

        row = result.data[0]

        # Get messages from Zep
        messages = []
        if self.zep_client:
            zep_messages = await self.zep_client.get_conversation_history(
                user_id=user_id or session_id,
                session_id=row.get('session_id'),
                limit=1000
            )
            messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "metadata": msg.metadata
                }
                for msg in zep_messages
            ]

        # Parse JSONB fields
        preferences = row.get('preferences_json', {})
        vehicles = row.get('vehicles_discussed', [])

        if isinstance(preferences, str):
            preferences = json.loads(preferences)
        if isinstance(vehicles, str):
            vehicles = json.loads(vehicles)

        return ConversationExportData(
            conversation_id=row.get('id'),
            session_id=row.get('session_id'),
            user_id=row.get('user_id'),
            title=row.get('title', ''),
            summary=row.get('summary', ''),
            started_at=row.get('started_at'),
            ended_at=row.get('last_message_at'),
            message_count=row.get('message_count', 0),
            preferences=preferences,
            vehicles_discussed=vehicles,
            journey_stage=row.get('journey_stage', 'discovery'),
            evolution_detected=row.get('evolution_detected', False),
            messages=messages
        )

    async def _get_all_conversations_for_user(
        self,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> List[ConversationExportData]:
        """Fetch all conversations for a user/session"""
        query = self.supabase_client.table('conversation_history').select('*')

        if user_id:
            query = query.eq('user_id', user_id)
        else:
            query = query.is_('user_id', 'null').eq('session_id', session_id)

        query = query.not_eq('status', 'deleted').order('started_at', desc=True)

        result = query.execute()

        conversations = []
        for row in result.data:
            # Convert to ConversationExportData
            preferences = row.get('preferences_json', {})
            vehicles = row.get('vehicles_discussed', [])

            if isinstance(preferences, str):
                preferences = json.loads(preferences)
            if isinstance(vehicles, str):
                vehicles = json.loads(vehicles)

            conversations.append(ConversationExportData(
                conversation_id=row.get('id'),
                session_id=row.get('session_id'),
                user_id=row.get('user_id'),
                title=row.get('title', ''),
                summary=row.get('summary', ''),
                started_at=row.get('started_at'),
                ended_at=row.get('last_message_at'),
                message_count=row.get('message_count', 0),
                preferences=preferences,
                vehicles_discussed=vehicles,
                journey_stage=row.get('journey_stage', 'discovery'),
                evolution_detected=row.get('evolution_detected', False),
                messages=[]  # Messages would be fetched separately if needed
            ))

        return conversations

    async def _generate_conversation_pdf(
        self,
        data: ConversationExportData,
        file_path: Path
    ):
        """Generate formatted PDF from conversation data"""
        if not self.pdf_available:
            raise RuntimeError("PDF generation not available")

        # Create PDF
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=20
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#333333'),
            spaceAfter=12
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY
        )

        # Build PDF content
        story = []

        # Title
        story.append(Paragraph(data.title, title_style))
        story.append(Spacer(1, 12))

        # Metadata table
        metadata_data = [
            ['Date:', data.started_at.strftime('%B %d, %Y')],
            ['Messages:', str(data.message_count)],
            ['Journey Stage:', data.journey_stage.title()],
            ['Session ID:', data.session_id[:8] + '...']
        ]
        metadata_table = Table(metadata_data, colWidths=[1.5*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#666666')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd'))
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 20))

        # Summary
        story.append(Paragraph("Summary", heading_style))
        story.append(Paragraph(data.summary, normal_style))
        story.append(Spacer(1, 20))

        # Preferences
        if data.preferences:
            story.append(Paragraph("Your Preferences", heading_style))
            for category, values in data.preferences.items():
                if values:
                    if isinstance(values, list):
                        values_str = ', '.join(str(v) for v in values)
                    else:
                        values_str = str(values)
                    story.append(Paragraph(f"<b>{category.title()}:</b> {values_str}", normal_style))
            story.append(Spacer(1, 20))

        # Vehicles discussed
        if data.vehicles_discussed:
            story.append(Paragraph("Vehicles Discussed", heading_style))
            for vehicle in data.vehicles_discussed[:5]:  # Limit to top 5
                make = vehicle.get('make', '')
                model = vehicle.get('model', '')
                year = vehicle.get('year', '')
                relevance = vehicle.get('relevance_score', 0)
                story.append(
                    Paragraph(
                        f"• {year} {make} {model} ({int(relevance*100)}% relevant)",
                        normal_style
                    )
                )
            story.append(Spacer(1, 20))

        # Messages (last 20)
        if data.messages:
            story.append(Paragraph("Conversation", heading_style))
            story.append(PageBreak())

            for msg in data.messages[-20:]:  # Last 20 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                timestamp = msg.get('created_at', '')

                # Format message
                role_label = "You" if role == 'user' else "Otto"
                role_color = "#1a73e8" if role == 'user' else "#34a853"

                # Add role label
                role_para = Paragraph(
                    f'<font color="{role_color}"><b>{role_label}:</b></font>',
                    normal_style
                )
                story.append(role_para)

                # Add message content
                content_para = Paragraph(content, normal_style)
                story.append(content_para)

                # Add timestamp if available
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime('%I:%M %p')
                        story.append(Paragraph(f'<font size="8">{time_str}</font>', normal_style))
                    except:
                        pass

                story.append(Spacer(1, 12))

        # Footer
        story.append(PageBreak())
        story.append(Paragraph(
            f"<font size='8' color='#666'>Export generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</font>",
            normal_style
        ))

        # Build PDF
        doc.build(story)

    async def _compile_preferences_summary(
        self,
        conversations: List[ConversationExportData]
    ) -> Dict[str, Any]:
        """Compile aggregate preferences across all conversations"""
        all_preferences = {}

        for conv in conversations:
            for category, values in conv.preferences.items():
                if category not in all_preferences:
                    all_preferences[category] = []

                if isinstance(values, list):
                    all_preferences[category].extend(values)
                else:
                    all_preferences[category].append(values)

        # Deduplicate
        for category in all_preferences:
            all_preferences[category] = list(set(all_preferences[category]))

        return all_preferences

    async def _compile_all_vehicles(
        self,
        conversations: List[ConversationExportData]
    ) -> List[Dict[str, Any]]:
        """Compile all vehicles mentioned across conversations"""
        all_vehicles = []

        for conv in conversations:
            for vehicle in conv.vehicles_discussed:
                if vehicle not in all_vehicles:
                    all_vehicles.append(vehicle)

        return all_vehicles

    async def _create_export_record(
        self,
        export_type: str,
        conversation_ids: List[str],
        user_id: Optional[str],
        session_id: Optional[str],
        file_path: str,
        file_size_bytes: int
    ) -> Dict[str, Any]:
        """Create export record in database for tracking"""
        try:
            export_data = {
                'export_type': export_type,
                'conversation_ids': conversation_ids,
                'file_path': file_path,
                'file_size_bytes': file_size_bytes,
                'download_count': 0,
                'request_type': 'user_request',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat()
            }

            if user_id:
                export_data['user_id'] = user_id
            if session_id:
                export_data['session_id'] = session_id

            result = self.supabase_client.table('conversation_exports').insert(export_data).execute()

            if result.data:
                return result.data[0]

            return {}

        except Exception as e:
            logger.error(f"Failed to create export record: {e}")
            return {}

    async def get_export(
        self,
        export_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get export record and verify access"""
        try:
            query = self.supabase_client.table('conversation_exports').select('*').eq('id', export_id)

            if user_id:
                query = query.eq('user_id', user_id)
            elif session_id:
                query = query.is_('user_id', 'null').eq('session_id', session_id)

            result = query.execute()

            if result.data:
                export = result.data[0]

                # Increment download count
                self.supabase_client.table('conversation_exports').update({
                    'download_count': export.get('download_count', 0) + 1,
                    'last_downloaded_at': datetime.now().isoformat()
                }).eq('id', export_id).execute()

                return export

            return None

        except Exception as e:
            logger.error(f"Failed to get export: {e}")
            return None

    async def cleanup_expired_exports(self):
        """Remove expired export files (background task)"""
        try:
            # Find expired exports
            now = datetime.now()
            result = self.supabase_client.table('conversation_exports').select('*').lt('expires_at', now.isoformat()).execute()

            for export in result.data:
                file_path = export.get('file_path')
                if file_path:
                    path = Path(file_path)
                    if path.exists():
                        path.unlink()
                        logger.info(f"Deleted expired export: {file_path}")

            # Delete records
            # (Would be done in a real implementation)
            logger.info(f"Cleaned up {len(result.data)} expired exports")

        except Exception as e:
            logger.error(f"Failed to cleanup expired exports: {e}")


# Singleton instance
_export_service_instance: Optional[ConversationExportService] = None


def get_export_service(
    storage_path: str = "exports/conversations",
    supabase_client=None,
    zep_client: Optional[ZepClient] = None
) -> ConversationExportService:
    """Get or create singleton ConversationExportService instance"""
    global _export_service_instance

    if _export_service_instance is None:
        _export_service_instance = ConversationExportService(
            storage_path=storage_path,
            supabase_client=supabase_client,
            zep_client=zep_client
        )

    return _export_service_instance
