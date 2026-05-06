import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Skull, 
  ShieldAlert, 
  Zap,
  Info,
  ArrowRight,
  Loader2
} from 'lucide-react';

const API_BASE = "http://localhost:8000";
const PAGE_SIZE = 100;

const App = () => {
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [streamedComments, setStreamedComments] = useState([]);
  const [error, setError] = useState("");
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const scrollRef = useRef(null);
  const sentinelRef = useRef(null);

  const [targetUser] = useState("hannahgidey");
  const [searchQuery, setSearchQuery] = useState("");

  const seenKeys = useRef(new Set());

  // ── Load a page of history ────────────────────────────────
  const loadHistory = useCallback(async (currentOffset = 0, append = false) => {
    if (!append) setInitialLoading(true);
    else setLoadingMore(true);

    try {
      const resp = await fetch(
        `${API_BASE}/history?username=${targetUser}&limit=${PAGE_SIZE}&offset=${currentOffset}`
      );
      const data = await resp.json();

      if (data.status === "success") {
        setTotal(data.total ?? 0);
        const newComments = data.comments.map((c, i) => ({
          ...c,
          id: `HG-${String(currentOffset + i + 1).padStart(5, '0')}`,
        }));

        // Track seen keys for dedup against stream
        newComments.forEach(c => {
          seenKeys.current.add(`${c.user}-${c.video_id}-${c.text}`);
        });

        if (append) {
          setStreamedComments(prev => [...prev, ...newComments]);
        } else {
          setStreamedComments(newComments);
        }
        setOffset(currentOffset + newComments.length);
      } else {
        if (!append) setStreamedComments([]);
      }
    } catch (e) {
      console.error("Failed to fetch history:", e);
    } finally {
      setInitialLoading(false);
      setLoadingMore(false);
    }
  }, [targetUser]);

  // ── Initial load ──────────────────────────────────────────
  useEffect(() => {
    loadHistory(0, false);
  }, [loadHistory]);

  // ── Infinite scroll via IntersectionObserver ──────────────
  useEffect(() => {
    if (!sentinelRef.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (
          entry.isIntersecting &&
          !loading &&
          !loadingMore &&
          !initialLoading &&
          offset < total &&
          !searchQuery // Don't paginate while searching
        ) {
          loadHistory(offset, true);
        }
      },
      { root: scrollRef.current, rootMargin: "400px" }
    );

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [offset, total, loading, loadingMore, initialLoading, searchQuery, loadHistory]);

  // ── Stream fresh data from TikTok ─────────────────────────
  const fetchFresh = async (username = targetUser) => {
    if (loading) return;
    setLoading(true);
    setError("");
    const cleanUser = username.replace('@', '');

    try {
      const response = await fetch(`${API_BASE}/analyze_stream?username=${cleanUser}`);
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.error) {
              setError(data.error);
            } else {
              const key = `${data.user}-${data.video_id}-${data.text}`;
              if (!seenKeys.current.has(key)) {
                seenKeys.current.add(key);
                setStreamedComments(prev => {
                  const newId = `HG-${String(prev.length + 1).padStart(5, '0')}`;
                  return [...prev, { ...data, id: newId }];
                });
                setTotal(prev => prev + 1);
              }
            }
          } catch (e) {
            console.error("Error parsing stream line:", e);
          }
        }
      }
    } catch (err) {
      setError("Stream interrupted.");
    } finally {
      setLoading(false);
    }
  };

  // Auto-scroll during live streaming
  useEffect(() => {
    if (scrollRef.current && loading) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamedComments, loading]);

  // ── Filter by search ──────────────────────────────────────
  const filteredComments = streamedComments.filter(c => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.user.toLowerCase().includes(q) || 
      (c.nickname && c.nickname.toLowerCase().includes(q)) ||
      c.id.toLowerCase().includes(q) ||
      (c.text && c.text.toLowerCase().includes(q))
    );
  });

  const hasMore = offset < total && !searchQuery;

  return (
    <div className="relative h-screen bg-[#F8F9FA] flex flex-col items-center overflow-hidden">
      {/* Glassmorphic Background Blobs */}
      <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-pink-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-[-10%] right-[-5%] w-[30%] h-[30%] bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Modern Glass Header */}
      <header className="w-full premium-glass sticky top-0 z-50 border-b border-white/20">
        <div className="max-w-7xl mx-auto px-8 py-8 flex flex-col md:flex-row items-center justify-between gap-8">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-8"
          >
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-tr from-pink-500 to-purple-600 rounded-[2rem] blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
              <div className="relative w-20 h-20 rounded-[2rem] bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center shadow-2xl overflow-hidden">
                <span className="text-3xl font-black text-white italic tracking-tighter">HG</span>
                <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <motion.div 
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute -bottom-1 -right-1 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-lg"
              >
                <div className="w-3 h-3 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)]" />
              </motion.div>
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center gap-3 mb-1">
                <div className="h-[1px] w-8 bg-pink-500/40" />
                <span className="text-[10px] font-black text-pink-500/60 uppercase tracking-[0.5em]">Exclusive</span>
              </div>
              <h1 className="text-5xl font-black tracking-tighter text-black leading-none">
                HANNAH <span className="gradient-text italic uppercase">GIDEY</span>
              </h1>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-[9px] font-bold text-black/80 tracking-[0.3em] uppercase">Historical Archive</span>
                <div className="w-1 h-1 rounded-full bg-black/20" />
                <span className="text-[9px] font-bold text-black/70 tracking-[0.3em] uppercase">v2.0 Stable</span>
              </div>
            </div>
          </motion.div>

          <div className="flex flex-1 max-w-lg mx-12 items-center gap-6">
            <div className="flex-1 relative group">
              <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-black/60 group-focus-within:text-pink-500 transition-colors">
                <Search size={18} />
              </div>
              <input 
                type="text" 
                placeholder="Search Archive..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white/40 backdrop-blur-md border border-white/40 outline-none pl-14 pr-6 py-4 rounded-3xl text-sm font-semibold placeholder:text-black/60 focus:ring-4 ring-pink-500/10 transition-all shadow-inner"
              />
            </div>
          </div>

          <div className="flex items-center gap-12">
            <div className="flex flex-col items-center">
              <span className="text-[10px] font-black text-black uppercase tracking-[0.5em] mb-2">Total Logs</span>
              <div className="px-6 py-2 rounded-2xl bg-black/5 border border-black/10 shadow-sm">
                <span className="text-3xl font-black text-black tracking-tighter">
                  {(total || 0).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 4-Column Grid Stream Area */}
      <main 
        ref={scrollRef}
        className="w-full max-w-7xl flex-1 px-8 pb-32 overflow-y-auto custom-scrollbar"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
          <AnimatePresence initial={false}>
            {initialLoading ? (
              [...Array(12)].map((_, i) => (
                <motion.div key={`init-skeleton-${i}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <SkeletonCard />
                </motion.div>
              ))
            ) : (
              filteredComments.map((comment) => (
                <motion.div
                  key={comment.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="w-full h-fit"
                >
                  <CommentCard comment={comment} />
                </motion.div>
              ))
            )}
            
            {/* Loading skeletons during stream or pagination */}
            {(loading || loadingMore) && [...Array(4)].map((_, i) => (
              <motion.div
                key={`skeleton-${i}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="w-full"
              >
                <SkeletonCard />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Infinite scroll sentinel */}
        <div ref={sentinelRef} className="w-full h-4" />

        {/* Loading more indicator */}
        {loadingMore && (
          <div className="w-full flex justify-center py-6">
            <div className="flex items-center gap-3 text-black/40 text-sm font-semibold">
              <Loader2 className="animate-spin" size={16} />
              Loading more comments...
            </div>
          </div>
        )}

        {/* End of archive indicator */}
        {!hasMore && !initialLoading && streamedComments.length > 0 && !searchQuery && (
          <div className="w-full flex justify-center py-8">
            <span className="text-[11px] font-black text-black/20 uppercase tracking-[0.3em]">
              End of Archive — {(total || 0).toLocaleString()} comments loaded
            </span>
          </div>
        )}
        
        <div className="w-full flex justify-center pt-8 pb-24">
          <button 
            onClick={fetchFresh}
            disabled={loading || initialLoading}
            className="group relative px-12 py-5 bg-[#1A1A1A] text-white rounded-3xl font-black text-[12px] uppercase tracking-[0.3em] shadow-2xl hover:shadow-pink-500/30 hover:-translate-y-1 transition-all active:translate-y-0 disabled:opacity-50 overflow-hidden"
          >
            <span className="relative z-10 flex items-center gap-4">
              {loading ? <Zap className="animate-spin text-pink-400" size={16} /> : <Zap className="text-pink-400" size={16} />}
              {loading ? 'Fetching New Logs...' : 'Scan For Fresh Data'}
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-pink-500 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        </div>
      </main>

      {/* Stats overlay */}
      <div className="fixed bottom-8 left-8 z-20">
        <div className="minimal-glass p-4 rounded-2xl flex flex-col gap-1 border border-black/5">
          <span className="text-[10px] font-black text-black/60 uppercase tracking-widest">Loaded / Total</span>
          <span className="text-2xl font-black gradient-text">
            {streamedComments.length.toLocaleString()} / {(total || 0).toLocaleString()}
          </span>
        </div>
      </div>

      <div className="fixed bottom-0 left-0 w-full h-32 bg-gradient-to-t from-[#F8F9FA] to-transparent pointer-events-none" />
    </div>
  );
};

const SkeletonCard = () => (
  <div className="w-full p-6 rounded-2xl border border-black/5 bg-white animate-pulse">
    <div className="flex justify-between items-start mb-3">
      <div className="flex flex-col gap-2">
        <div className="h-4 w-24 bg-gray-100 rounded-md" />
        <div className="h-3 w-16 bg-gray-50 rounded-md" />
      </div>
      <div className="h-4 w-12 bg-gray-50 rounded-md" />
    </div>
    <div className="space-y-2 mt-4">
      <div className="h-3 w-full bg-gray-100 rounded-md" />
      <div className="h-3 w-4/5 bg-gray-50 rounded-md" />
    </div>
  </div>
);

const CommentCard = ({ comment }) => (
  <div className="w-full p-6 rounded-2xl border border-black/5 bg-white hover:border-pink-500/20 hover:shadow-lg transition-all group relative overflow-hidden">
    <div className="absolute top-0 right-0 px-3 py-1 bg-gray-50 text-[10px] font-black text-black/80 tracking-tighter rounded-bl-xl border-l border-b border-black/5">
      <span className="font-bold">{comment.id}</span>
    </div>
    <div className="flex justify-between items-start mb-3">
      <div className="flex flex-col">
        <span className="text-sm font-black tracking-tight text-black leading-tight">
          {comment.nickname || comment.user}
        </span>
        <a 
          href={`https://www.tiktok.com/@${comment.user}`} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-[10px] font-bold text-pink-600 hover:text-pink-700 uppercase tracking-tighter transition-colors flex items-center gap-1 mt-1 group/link"
        >
          @{comment.user}
          <ArrowRight size={8} className="opacity-0 group-hover/link:opacity-100 transition-opacity" />
        </a>
      </div>
    </div>
    <div className="mt-3">
      {comment.sticker_url ? (
        <div className="rounded-lg overflow-hidden border border-black/5 bg-gray-50 flex justify-center p-2">
          <img 
            src={comment.sticker_url} 
            alt="Sticker" 
            className="max-h-20 object-contain"
          />
        </div>
      ) : (
        <p className="text-sm font-medium leading-relaxed text-black">
          {comment.text}
        </p>
      )}
    </div>
  </div>
);

export default App;
