/**
 * WelcomeScreen.jsx
 *
 * Post-login welcome: dark theme, centered card with title and
 * one primary CTA to start the kiosk flow. Framer Motion: fade-in,
 * card slide-up, button hover scale. Touch-friendly.
 */

import { motion } from "framer-motion";

export default function WelcomeScreen({ onStart }) {
  return (
    <motion.div
      className="min-h-screen w-full flex items-center justify-center p-6"
      style={{ backgroundColor: "#0A0A0A" }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <motion.div
        className="w-full max-w-lg rounded-2xl p-8 md:p-12 text-center"
        style={{ backgroundColor: "#141414" }}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
      >
        <h1 className="text-2xl md:text-3xl font-semibold text-white tracking-tight mb-2">
          Welcome
        </h1>
        <p className="text-white/60 text-base md:text-lg mb-8">
          Ready to create your wedding photo?
        </p>
        <motion.button
          type="button"
          onClick={onStart}
          className="min-h-[56px] md:min-h-[60px] w-full max-w-sm mx-auto rounded-xl bg-white text-black font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-[#141414]"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ type: "spring", stiffness: 400, damping: 17 }}
        >
          Start
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
