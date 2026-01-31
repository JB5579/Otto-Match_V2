import React, { useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';
import type { Vehicle } from '../../app/types/api';
import { VehicleImageCarousel } from './VehicleImageCarousel';
import { VehicleSpecsDetail } from './VehicleSpecsDetail';
import { KeyFeatures } from './KeyFeatures';
import { OttoRecommendation } from './OttoRecommendation';
import { SocialProofBadges } from './SocialProofBadges';
import { PricingPanel } from './PricingPanel';
import { ModalActionButtons } from './ModalActionButtons';
import './VehicleDetailModal.css';

interface VehicleDetailModalProps {
  vehicle: Vehicle | null;
  isOpen: boolean;
  onClose: () => void;
  onHold?: (vehicleId: string) => void;
  onCompare?: (vehicleId: string) => void;
}

/**
 * VehicleDetailModal - Comprehensive vehicle detail modal
 *
 * Features:
 * - Image carousel with thumbnail navigation (AC3)
 * - Vehicle specifications display (AC4)
 * - Otto's personalized recommendation (AC5)
 * - Social proof badges (AC6)
 * - Action buttons for hold/compare (AC7)
 * - Responsive layout (AC11)
 * - Backdrop blur effect (12px)
 * - Glass-morphism styling
 * - Smooth animations (0.3s spring)
 *
 * @param props - Component props
 * @returns Vehicle detail modal component
 */
export const VehicleDetailModal: React.FC<VehicleDetailModalProps> = ({
  vehicle,
  isOpen,
  onClose,
  onHold,
  onCompare,
}) => {
  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!vehicle) return null;

  const title = `${vehicle.year} ${vehicle.make} ${vehicle.model}${vehicle.trim ? ` ${vehicle.trim}` : ''}`;
  const images = vehicle.images || [];

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        {/* Backdrop with 12px blur */}
        <Dialog.Overlay asChild>
          <motion.div
            className="fixed inset-0 z-50 bg-black/40"
            style={{
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)'
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
        </Dialog.Overlay>

        {/* Modal Content - 900px max-width, glass-morphism */}
        <Dialog.Content asChild>
          <motion.div
            className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 vehicleDetailModalContent"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{
              type: 'spring',
              stiffness: 300,
              damping: 25,
              duration: 0.3,
            }}
          >
            {/* Header */}
            <div className="modalHeader">
              <Dialog.Title className="modalTitle">
                {title}
              </Dialog.Title>
              <Dialog.Close asChild>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="closeButton"
                  aria-label="Close modal"
                >
                  <X size={20} />
                </motion.button>
              </Dialog.Close>
            </div>

            {/* Scrollable Content */}
            <div className="modalScrollableContent">
              {/* Image Carousel */}
              {images.length > 0 && (
                <VehicleImageCarousel images={images} title={title} />
              )}

              {/* Two Column Layout */}
              <div className="twoColumnLayout">
                {/* Left Column */}
                <div className="columnContainer leftColumn">
                  {/* Specifications */}
                  <VehicleSpecsDetail vehicle={vehicle} />

                  {/* Features */}
                  {vehicle.features && vehicle.features.length > 0 && (
                    <KeyFeatures features={vehicle.features} maxDisplay={8} />
                  )}

                  {/* Description */}
                  {vehicle.description && (
                    <div className="vehicleDescription">
                      <h4 className="sectionTitle">
                        About this Vehicle
                      </h4>
                      <p className="descriptionText">
                        {vehicle.description}
                      </p>
                    </div>
                  )}
                </div>

                {/* Right Column */}
                <div className="columnContainer rightColumn">
                  {/* Otto Recommendation */}
                  <OttoRecommendation
                    recommendation={vehicle.ottoRecommendation}
                    matchScore={vehicle.matchScore}
                  />

                  {/* Social Proof Badges */}
                  <SocialProofBadges
                    currentViewers={vehicle.currentViewers}
                  />

                  {/* Pricing Panel */}
                  <PricingPanel
                    price={vehicle.price}
                    originalPrice={vehicle.originalPrice}
                    savings={vehicle.savings}
                    availabilityStatus={vehicle.availabilityStatus}
                  />

                  {/* Action Buttons */}
                  <ModalActionButtons
                    vehicleId={vehicle.id}
                    availabilityStatus={vehicle.availabilityStatus}
                    onHold={onHold}
                    onCompare={onCompare}
                  />
                </div>
              </div>
            </div>

            {/* Hidden description for screen readers */}
            <Dialog.Description className="sr-only">
              Detailed information about {title} including images, specifications, features, pricing, and Otto's personalized recommendation.
            </Dialog.Description>
          </motion.div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default VehicleDetailModal;
