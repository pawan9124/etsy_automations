"use client";

import React, { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, CheckCircle2, Loader2, Sparkles, Lock, ArrowRight, Video, Play, Image as ImageIcon, LayoutGrid, Zap, X, Download } from "lucide-react";
import JSZip from "jszip";
import { saveAs } from "file-saver";

type UploadState = "idle" | "processing" | "completed";

const LOADING_TEXTS = [
  "Warping 2D to 3D cylinder...",
  "Applying dynamic lighting...",
  "Generating 10-page layout grid...",
  "Rendering final assets...",
];

export default function MockupPipeline() {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [files, setFiles] = useState<File[]>([]);
  const [loadingTextIndex, setLoadingTextIndex] = useState(0);
  const [heroImageUrl, setHeroImageUrl] = useState<string | null>(null);
  const [lifestyleImageUrl, setLifestyleImageUrl] = useState<string | null>(null);
  const [closeupImageUrl, setCloseupImageUrl] = useState<string | null>(null);
  const [flatImageUrl, setFlatImageUrl] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  
  const [isCapturing, setIsCapturing] = useState(false);
  const [isLeadCaptured, setIsLeadCaptured] = useState(false);

  const [leadForm, setLeadForm] = useState({
    name: "",
    email: "",
    etsyUrl: "",
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Limit to 4 files total
    setFiles((prev) => [...prev, ...acceptedFiles].slice(0, 4));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
    maxFiles: 4,
  });

  // Cycle loading text
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (uploadState === "processing") {
      interval = setInterval(() => {
        setLoadingTextIndex((prev) => (prev + 1) % LOADING_TEXTS.length);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [uploadState]);

  // Wake up Render backend on page load
  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_BASE}/api/health`).catch(() => {
      // Silently fail if it takes a while to wake up
    });
  }, []);

  const generateMockups = async () => {
    if (files.length === 0) return;
    setUploadState("processing");
    setLoadingTextIndex(0);

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });

      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_BASE}/api/generate-teaser`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to generate from API");
      }

      // Read JSON payload containing base64 images
      const data = await response.json();
      
      setHeroImageUrl(data.hero);
      setCloseupImageUrl(data.closeup);
      setLifestyleImageUrl(data.lifestyle);
      
      // If they uploaded multiple files, use a different one for the flat preview
      const flatFile = files.length > 3 ? files[3] : files.length > 1 ? files[1] : files[0];
      setFlatImageUrl(URL.createObjectURL(flatFile));
      
    } catch (error) {
      console.error(error);
      alert("Failed to connect to the backend server. Please make sure the FastAPI server is running on port 8000.");
      setUploadState("idle");
      return;
    } finally {
      setUploadState("completed");
    }
  };

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCapturing(true);

    try {
      // 1. Save lead to backend
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_BASE}/api/capture-lead`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(leadForm),
      });

      if (!response.ok) throw new Error("Failed to save lead");

      // 2. Create Zip file with generated base64 images
      const zip = new JSZip();
      
      const stripBase64 = (dataUrl: string) => dataUrl.split(",")[1];

      if (heroImageUrl) zip.file("1_Hero_360_View.png", stripBase64(heroImageUrl), { base64: true });
      if (lifestyleImageUrl) zip.file("2_Lifestyle_Mockup.png", stripBase64(lifestyleImageUrl), { base64: true });
      if (closeupImageUrl) zip.file("3_Closeup_Detail.png", stripBase64(closeupImageUrl), { base64: true });

      const content = await zip.generateAsync({ type: "blob" });
      
      // 3. Trigger download
      saveAs(content, "MockupPipeline_Sample.zip");

      // 4. Show success screen
      setIsLeadCaptured(true);
    } catch (error) {
      console.error("Lead capture failed:", error);
      alert("Failed to unlock. Please try again.");
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-emerald-500/30">
      {/* Header */}
      <header className="border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight hover:opacity-80 transition-opacity cursor-pointer">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            <span>Mockup<span className="text-zinc-500">Pipeline</span></span>
          </a>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 pt-20 pb-32">
        
        {/* HERO COPY (Shown only in idle/processing) */}
        <AnimatePresence mode="wait">
          {uploadState !== "completed" && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center mb-16"
            >
              <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 bg-gradient-to-br from-white to-zinc-500 bg-clip-text text-transparent">
                Turn Flat Wraps into a 10-Page Etsy Listing Suite in 60 Seconds.
              </h1>
              <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
                Skip the Canva layout grind. Drop your designs below to see the magic. 
                We automatically generate 3D mockups, size guides, close-ups, and a 360° marketing video.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* STATE 1: IDLE / UPLOAD */}
        {uploadState === "idle" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-2xl mx-auto"
          >
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
                isDragActive
                  ? "border-emerald-500 bg-emerald-500/10"
                  : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 hover:bg-zinc-900"
              }`}
            >
              <input {...getInputProps()} />
              <UploadCloud className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
              <p className="text-zinc-300 font-medium mb-1">
                Drag & drop up to 4 wraps here
              </p>
              <p className="text-sm text-zinc-500 mb-3">Supports .PNG or .JPG</p>
              <p className="text-xs text-emerald-500/80 bg-emerald-500/10 inline-block px-3 py-1 rounded-full">
                Tip: Upload horizontal wraps (~9.3" × 8.2") for best results
              </p>
            </div>

            {files.length > 0 && (
              <div className="mt-8">
                <div className="flex flex-wrap gap-4 justify-center mb-8">
                  {files.map((file, i) => (
                    <div key={i} className="relative group">
                      <img
                        src={URL.createObjectURL(file)}
                        alt={`upload-${i}`}
                        className="w-24 h-24 object-cover rounded-lg border border-zinc-800 shadow-xl"
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setFiles(files.filter((_, idx) => idx !== i));
                        }}
                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={generateMockups}
                  className="w-full sm:w-auto mx-auto flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold px-8 py-4 rounded-full transition-transform active:scale-95 shadow-[0_0_40px_-10px_rgba(16,185,129,0.5)]"
                >
                  <Sparkles className="w-5 h-5" />
                  Generate 3D Mockups (Free)
                </button>
              </div>
            )}
          </motion.div>
        )}

        {/* BEFORE & AFTER SECTION */}
        {uploadState === "idle" && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-20 w-full max-w-4xl mx-auto"
          >
            <div className="rounded-3xl overflow-hidden border border-zinc-800 shadow-2xl bg-zinc-900 group">
              <img src="/examples/before_after.jpg" alt="Before and After Automation" className="w-full h-auto object-cover group-hover:scale-[1.01] transition-transform duration-700" />
            </div>
          </motion.div>
        )}

        {/* FEATURES & EXAMPLES SECTION (Shown only in idle state) */}
        {uploadState === "idle" && (
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mt-32 pt-16 border-t border-zinc-800/50"
          >
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold mb-4">See What You Get instantly.</h2>
              <p className="text-zinc-400">Premium 3D rendering and professional layouts, fully automated.</p>
            </div>

            {/* Value Props Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
              <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-2xl">
                <div className="bg-emerald-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
                  <Zap className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">Zero Canva Skills Needed</h3>
                <p className="text-zinc-400 text-sm">Stop wrestling with clunky templates. Our engine builds perfect, print-ready layouts automatically.</p>
              </div>
              <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-2xl">
                <div className="bg-emerald-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
                  <LayoutGrid className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">Full Listing Generation</h3>
                <p className="text-zinc-400 text-sm">Generate polished, complete listing suites for your tumblers to avoid repetitive work. Get 10 or more optimized images perfectly tailored to your shop.</p>
              </div>
              <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-2xl">
                <div className="bg-emerald-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
                  <Play className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">360° Marketing Video</h3>
                <p className="text-zinc-400 text-sm">Stop the scroll with a premium, auto-generated rotating 3D video of your tumbler design.</p>
              </div>
            </div>

            {/* Example Assets Showcase */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
              
              {/* Left Column: Video */}
              <div className="lg:col-span-5 flex flex-col">
                <div className="flex items-center gap-2 mb-4 text-zinc-400">
                  <Video className="w-5 h-5" />
                  <span className="font-semibold tracking-wide uppercase text-sm">Auto-Generated Video</span>
                </div>
                <div className="rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-900 shadow-2xl relative group h-full min-h-[400px] lg:min-h-0 aspect-[4/5] lg:aspect-auto">
                  <video 
                    src="/examples/12_marketing_presentation.mp4" 
                    autoPlay 
                    loop 
                    muted 
                    playsInline
                    className="w-full h-full object-cover absolute inset-0"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent opacity-60 pointer-events-none"></div>
                </div>
              </div>

              {/* Right Column: Main Hero Image */}
              <div className="lg:col-span-7 flex flex-col">
                <div className="flex items-center gap-2 mb-4 text-zinc-400">
                  <ImageIcon className="w-5 h-5" />
                  <span className="font-semibold tracking-wide uppercase text-sm">360° Hero Mockup</span>
                </div>
                <div 
                  className="rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-900 shadow-2xl h-full flex items-center justify-center group cursor-pointer"
                  onClick={() => setSelectedImage("01_1_hero_single_wrap.png")}
                >
                  <img src="/examples/01_1_hero_single_wrap.png" alt="Main Hero" className="w-full h-auto object-contain group-hover:scale-105 transition-transform duration-700" />
                </div>
              </div>
            </div>

            {/* The Rest of the Suite */}
            <div className="mt-16">
              <div className="flex items-center gap-2 mb-6 justify-center text-zinc-400">
                <LayoutGrid className="w-5 h-5" />
                <span className="font-semibold tracking-wide uppercase text-sm">The Complete 10-Page Suite</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {[
                  "05_lifestyle_mockup.png",
                  "03_closeup_detail.png",
                  "04_flat_wrap.png",
                  "02_bundle_grid.png",
                  "06_what_you_get.png",
                  "07_color_palette.png",
                  "08_size_guide.png",
                  "09_multi_tumbler.png",
                  "10_thank_you.png",
                  "11_flat_bundle_preview.png"
                ].map((imgSrc, idx) => (
                  <div 
                    key={idx} 
                    className="rounded-xl overflow-hidden border border-zinc-800 bg-zinc-900 shadow-lg group cursor-pointer"
                    onClick={() => setSelectedImage(imgSrc)}
                  >
                    <img 
                      src={`/examples/${imgSrc}`} 
                      alt={`Suite Image ${idx}`} 
                      className="w-full h-auto object-cover group-hover:scale-105 transition-transform duration-500" 
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Custom Theme Banner */}
            <div className="mt-24 p-8 rounded-2xl bg-gradient-to-r from-zinc-900 to-zinc-900/50 border border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
              <div className="relative z-10">
                <div className="inline-block px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider rounded-full mb-4">
                  Enterprise
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Need a specialized theme for your shop?</h3>
                <p className="text-zinc-400 text-sm max-w-2xl leading-relaxed">
                  This page is a live demo of our standard 10-page Etsy suite. If you require a unique brand aesthetic, specific mockup angles, or a completely custom 3D environment, we can build a bespoke automation engine exclusively for your store.
                </p>
              </div>
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  navigator.clipboard.writeText("xfantasypro@gmail.com");
                  alert("Email address copied to clipboard: xfantasypro@gmail.com");
                }}
                className="relative z-10 whitespace-nowrap px-6 py-3 bg-zinc-100 hover:bg-white text-zinc-950 font-bold rounded-lg transition-colors shadow-lg flex items-center justify-center cursor-pointer"
              >
                Request Customization
              </button>
            </div>

          </motion.div>
        )}

        {/* STATE 2: PROCESSING */}
        {uploadState === "processing" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center py-20"
          >
            <Loader2 className="w-16 h-16 text-emerald-500 animate-spin mb-8" />
            <AnimatePresence mode="wait">
              <motion.p
                key={loadingTextIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-xl font-medium text-zinc-300"
              >
                {LOADING_TEXTS[loadingTextIndex]}
              </motion.p>
            </AnimatePresence>
            
            {/* Fake progress bar */}
            <div className="w-64 h-1 bg-zinc-900 rounded-full mt-8 overflow-hidden">
              <motion.div 
                className="h-full bg-emerald-500"
                initial={{ width: "0%" }}
                animate={{ width: "100%" }}
                transition={{ duration: 5, ease: "easeInOut" }}
              />
            </div>
          </motion.div>
        )}

        {/* STATE 3: COMPLETED (TEASER & LEAD CAPTURE) */}
        {uploadState === "completed" && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full"
          >
            {/* Success Banner */}
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 flex items-center gap-3 text-emerald-400 mb-8 max-w-2xl mx-auto">
              <CheckCircle2 className="w-6 h-6 flex-shrink-0" />
              <p className="font-medium">Generation Complete! Here is your free Hero Image.</p>
            </div>

            {/* Top Section: The Hook (Actual Generated Image) */}
            <div className="mb-12 relative group rounded-2xl overflow-hidden border border-zinc-800 shadow-2xl bg-zinc-900">
              {heroImageUrl ? (
                <img src={heroImageUrl} alt="Generated Hero Mockup" className="w-full h-auto object-contain" />
              ) : (
                <div className="w-full aspect-[4/3] bg-zinc-900 flex items-center justify-center">
                  <span className="text-zinc-600">Image Failed to Load</span>
                </div>
              )}
            </div>

            {/* Bottom Section: The Gate (Blurred Grid & Lead Form) */}
            <div className="relative rounded-3xl overflow-hidden bg-zinc-950 border border-zinc-800 p-1">
              
              {/* Background Grid (No Blur) */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 opacity-50 pointer-events-none select-none">
                {/* 1. Top Left: Lifestyle Mockup (Dynamic) */}
                <div className="aspect-square bg-zinc-900 rounded-xl overflow-hidden border border-zinc-700">
                  <img src={lifestyleImageUrl || "/examples/05_lifestyle_mockup.png"} alt="Lifestyle" className="w-full h-full object-cover" />
                </div>
                {/* 2. Top Center: Default (Covered by modal) */}
                <div className="aspect-square bg-zinc-900 rounded-xl overflow-hidden border border-zinc-700">
                  <img src="/examples/08_size_guide.png" alt="Grid placeholder" className="w-full h-full object-cover" />
                </div>
                {/* 3. Top Right: Flat Wrap (Dynamic) */}
                <div className="aspect-square bg-zinc-900 rounded-xl overflow-hidden border border-zinc-700">
                  <img src={flatImageUrl || "/examples/04_flat_wrap.png"} alt="Flat Wrap" className="w-full h-full object-contain p-2" />
                </div>
                {/* 4. Bottom Left: What You Get (Default) */}
                <div className="aspect-square bg-zinc-900 rounded-xl overflow-hidden border border-zinc-700">
                  <img src="/examples/06_what_you_get.png" alt="Grid placeholder" className="w-full h-full object-cover" />
                </div>
                {/* 5. Bottom Center: Default (Covered by modal) */}
                <div className="aspect-square bg-zinc-900 rounded-xl overflow-hidden border border-zinc-700">
                  <img src="/examples/07_color_palette.png" alt="Grid placeholder" className="w-full h-full object-cover" />
                </div>
                {/* 6. Bottom Right: Closeup Detail (Dynamic) */}
                <div className="aspect-square bg-zinc-900 rounded-xl overflow-hidden border border-zinc-700">
                  <img src={closeupImageUrl || "/examples/03_closeup_detail.png"} alt="Closeup" className="w-full h-full object-cover" />
                </div>
              </div>

              {/* Glassmorphic Lead Capture Card */}
              <div className="absolute inset-0 flex items-center justify-center p-4 sm:p-6 bg-zinc-950/80 backdrop-blur-sm z-10">
                <div className="bg-zinc-900/95 backdrop-blur-2xl border border-zinc-700/50 p-6 sm:p-8 rounded-2xl w-full max-w-lg shadow-2xl overflow-y-auto max-h-full">
                  
                  {isLeadCaptured ? (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Download className="w-8 h-8 text-emerald-400" />
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-4">Success! Your sample pack has downloaded.</h3>
                      <p className="text-zinc-300 mb-4 leading-relaxed">
                        To generate the remaining 7 images, the Size Guide, and the 360° marketing video for this design, please email us at <strong className="text-white">xfantasypro@gmail.com</strong> to discuss setting up a custom automation engine for your shop.
                      </p>
                      <div className="bg-zinc-950/50 rounded-lg p-4 mb-6 border border-zinc-800 text-left">
                        <p className="text-sm text-zinc-400">
                          <strong className="text-zinc-300 flex items-center gap-2 mb-1"><Lock className="w-4 h-4"/> Privacy Note:</strong> 
                          We do not permanently save your uploaded designs to protect your intellectual property. Please make sure to attach your original image file in the email so we can generate your remaining assets!
                        </p>
                      </div>
                      <button 
                        onClick={() => window.location.reload()}
                        className="bg-zinc-800 hover:bg-zinc-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                      >
                        Start Another Mockup
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-3 mb-6">
                        <Lock className="w-6 h-6 text-emerald-400" />
                        <h3 className="text-xl font-bold">Unlock Your Free Sample Pack</h3>
                      </div>
                      <p className="text-zinc-400 text-sm mb-6">
                        Your 3 custom generated mockups are ready. Enter your details to download them instantly, and request your full 10-page suite & 3D video!
                      </p>

                      <form className="space-y-4" onSubmit={handleUnlock}>
                        <div>
                          <input 
                            type="text" 
                            placeholder="Your Name" 
                            required
                            className="w-full bg-zinc-950/50 border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 transition-colors"
                            value={leadForm.name}
                            onChange={(e) => setLeadForm({...leadForm, name: e.target.value})}
                          />
                        </div>
                        <div>
                          <input 
                            type="email" 
                            placeholder="Email Address" 
                            required
                            className="w-full bg-zinc-950/50 border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 transition-colors"
                            value={leadForm.email}
                            onChange={(e) => setLeadForm({...leadForm, email: e.target.value})}
                          />
                        </div>
                        <div>
                          <input 
                            type="url" 
                            placeholder="Etsy Shop URL (Optional)" 
                            className="w-full bg-zinc-950/50 border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 transition-colors"
                            value={leadForm.etsyUrl}
                            onChange={(e) => setLeadForm({...leadForm, etsyUrl: e.target.value})}
                          />
                        </div>
                        <button
                          type="submit"
                          disabled={isCapturing}
                          className="w-full bg-white hover:bg-zinc-200 text-zinc-950 font-bold px-6 py-4 rounded-lg flex items-center justify-center gap-2 transition-colors mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isCapturing ? (
                            <>
                              <Loader2 className="w-5 h-5 animate-spin" />
                              Unlocking...
                            </>
                          ) : (
                            <>
                              Unlock & Download Free Sample
                              <ArrowRight className="w-5 h-5" />
                            </>
                          )}
                        </button>
                      </form>
                      <p className="text-center text-xs text-zinc-500 mt-6">
                        100% free. No credit card required.
                      </p>
                    </>
                  )}
                  
                </div>
              </div>
            </div>
            
          </motion.div>
        )}

      </main>

      {/* Footer */}
      <footer className="w-full py-8 text-center text-zinc-500 text-sm">
        <p>Questions? Contact us at <a href="mailto:xfantasypro@gmail.com" className="text-zinc-400 hover:text-white transition-colors underline decoration-zinc-700 underline-offset-4">xfantasypro@gmail.com</a></p>
      </footer>

      {/* Lightbox Modal */}
      <AnimatePresence>
        {selectedImage && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-zinc-950/90 backdrop-blur-sm p-4"
            onClick={() => setSelectedImage(null)}
          >
            <button 
              className="absolute top-6 right-6 text-white hover:text-zinc-300 transition-colors"
              onClick={() => setSelectedImage(null)}
            >
              <X className="w-8 h-8" />
            </button>
            <motion.img 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              src={`/examples/${selectedImage}`}
              alt="Zoomed preview"
              className="max-w-full max-h-full object-contain rounded-xl shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
