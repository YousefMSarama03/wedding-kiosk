import jerusalemStudioLogo from "../../assets/jerusalem-studio-logo.png";

export default function BrandLogo({ className = "", alt = "Jerusalem Studio logo" }) {
  return (
    <img
      src={jerusalemStudioLogo}
      alt={alt}
      className={`w-auto object-contain mix-blend-screen ${className}`}
    />
  );
}
