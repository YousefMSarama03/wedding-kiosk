import djLogo from "../../assets/dj-aldebwany-logo.png";
import jerusalemStudioLogo from "../../assets/jerusalem-studio-logo.png";

/**
 * Fixed partner marks: DJ (bottom-left), Jerusalem Studio (bottom-right).
 * No wrapper/image background. mix-blend-screen makes black pixels in the asset
 * disappear on dark kiosk backgrounds so only the light logo remains.
 */
export default function CornerLogos() {
  const imgClass =
    "h-[90px] w-auto max-w-[40vw] border-0 bg-transparent object-contain object-bottom shadow-none mix-blend-screen opacity-95 md:h-[100px] lg:h-[95px]";

  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-0 z-[60] flex items-end justify-between gap-3 bg-transparent px-3 pb-3 md:px-5 md:pb-4"
      aria-hidden
    >
      <img src={djLogo} alt="" className={imgClass} decoding="async" />
      <img src={jerusalemStudioLogo} alt="" className={imgClass} decoding="async" />
    </div>
  );
}
