'use client';

import Link from 'next/link';
import { ArrowLeft, Sparkles, Wand2, FileText, Briefcase, GraduationCap, Code, Lightbulb, User, Plus, Minus, Send, Loader2 } from 'lucide-react';
import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  api_polish_bullet, 
  api_tailor_resume, 
  api_generate_summary, 
  api_generate_jd 
} from '@/lib/api';
import { useDebounce } from '@/hooks/use-debounce';

interface ResumeData {
  summary: string;
  experience: { id: string; title: string; company: string; bullets: { id: string; text: string }[] }[];
  skills: string[];
  projects: { id: string; title: string; description: string; bullets: { id: string; text: string }[] }[];
}

interface AIResponse {
  success: boolean;
  data?: string;
  error?: string;
}

const sectionVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24, delay: 0.1 } },
};

const bulletVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 10 },
};

export default function ResumeBuilderPage() {
  const [resumeData, setResumeData] = useState<ResumeData>(() => {
    // Initialize with a unique ID for each bullet/project/experience
    const initialBulletId = () => Math.random().toString(36).substring(2, 9);
    return {
      summary: "Results-driven software engineer with 5 years of experience in full-stack development.",
      experience: [
        {
          id: initialBulletId(),
          title: "Senior Software Engineer",
          company: "TechCorp",
          bullets: [
            { id: initialBulletId(), text: "Developed and maintained critical microservices using Node.js and TypeScript." },
            { id: initialBulletId(), text: "Optimized database queries, reducing response times by 30%." },
            { id: initialBulletId(), text: "Mentored junior engineers on best practices." },
          ],
        },
      ],
      skills: ["React", "Node.js", "Python", "Django", "AWS", "Docker"],
      projects: [
        {
          id: initialBulletId(),
          title: "E-commerce Platform",
          description: "Built a scalable e-commerce platform from scratch.",
          bullets: [
            { id: initialBulletId(), text: "Implemented secure payment gateway integrations." },
            { id: initialBulletId(), text: "Designed a responsive user interface with React." },
          ],
        },
      ],
    };
  });

  const [activeTab, setActiveTab] = useState('input');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<AIResponse | null>(null);
  const [aiToolSelected, setAiToolSelected] = useState<string | null>(null);

  // For Job Description Generation
  const [jdTitle, setJdTitle] = useState('');
  const [jdCompany, setJdCompany] = useState('');
  const [jdExperience, setJdExperience] = useState('');
  const [jdLocation, setJdLocation] = useState('');
  const [jdWorkMode, setJdWorkMode] = useState('');
  const [jdSkills, setJdSkills] = useState('');
  const [jdNotes, setJdNotes] = useState('');

  // For Resume Tailoring
  const [jobDescription, setJobDescription] = useState('');

  // For Bullet Polishing
  const [bulletToPolish, setBulletToPolish] = useState('');
  const [polishRole, setPolishRole] = useState('');
  const [polishTechStack, setPolishTechStack] = useState('');
  const debouncedBullet = useDebounce(bulletToPolish, 500);
  const debouncedPolishRole = useDebounce(polishRole, 500);
  const debouncedPolishTechStack = useDebounce(polishTechStack, 500);

  // For Summary Generation
  const [summaryRole, setSummaryRole] = useState('');
  const [summaryExperience, setSummaryExperience] = useState('');
  const [summarySkills, setSummarySkills] = useState('');
  const [summaryCompanyType, setSummaryCompanyType] = useState('');

  const generateUniqueId = useCallback(() => Math.random().toString(36).substring(2, 9), []);

  // ── Handlers for dynamic sections ──
  const addExperience = useCallback(() => {
    setResumeData(prev => ({...prev, experience: [...prev.experience, { id: generateUniqueId(), title: '', company: '', bullets: [{ id: generateUniqueId(), text: '', }], }],}));
  }, [generateUniqueId]);
  const removeExperience = useCallback((id: string) => {
    setResumeData(prev => ({...prev, experience: prev.experience.filter(exp => exp.id !== id),}));
  }, []);
  const addExpBullet = useCallback((expId: string) => {
    setResumeData(prev => ({...prev, experience: prev.experience.map(exp =>
        exp.id === expId ? { ...exp, bullets: [...exp.bullets, { id: generateUniqueId(), text: '', }], } : exp,
      ),}));
  }, [generateUniqueId]);
  const removeExpBullet = useCallback((expId: string, bulletId: string) => {
    setResumeData(prev => ({...prev, experience: prev.experience.map(exp =>
        exp.id === expId ? { ...exp, bullets: exp.bullets.filter(b => b.id !== bulletId), } : exp,
      ),}));
  }, []);

  const addProject = useCallback(() => {
    setResumeData(prev => ({...prev, projects: [...prev.projects, { id: generateUniqueId(), title: '', description: '', bullets: [{ id: generateUniqueId(), text: '', }], }],}));
  }, [generateUniqueId]);
  const removeProject = useCallback((id: string) => {
    setResumeData(prev => ({...prev, projects: prev.projects.filter(proj => proj.id !== id),}));
  }, []);
  const addProjBullet = useCallback((projId: string) => {
    setResumeData(prev => ({...prev, projects: prev.projects.map(proj =>
        proj.id === projId ? { ...proj, bullets: [...proj.bullets, { id: generateUniqueId(), text: '', }], } : proj,
      ),}));
  }, [generateUniqueId]);
  const removeProjBullet = useCallback((projId: string, bulletId: string) => {
    setResumeData(prev => ({...prev, projects: prev.projects.map(proj =>
        proj.id === projId ? { ...proj, bullets: proj.bullets.filter(b => b.id !== bulletId), } : proj,
      ),}));
  }, []);

  // ── AI Tool Handlers ──
  const handleGenerateJd = useCallback(async () => {
    setAiLoading(true);
    setAiResult(null);
    setAiToolSelected('generate-jd');
    try {
      const result = await api_generate_jd({
        title: jdTitle,
        company: jdCompany,
        experience: jdExperience,
        location: jdLocation,
        work_mode: jdWorkMode,
        skills: jdSkills,
        additional_notes: jdNotes,
      });
      setAiResult({ success: true, data: result.data });
    } catch (e: any) {
      setAiResult({ success: false, error: e.message || 'Failed to generate JD.' });
    } finally {
      setAiLoading(false);
    }
  }, [jdTitle, jdCompany, jdExperience, jdLocation, jdWorkMode, jdSkills, jdNotes]);

  const handlePolishBullet = useCallback(async () => {
    setAiLoading(true);
    setAiResult(null);
    setAiToolSelected('polish-bullet');
    try {
      const result = await api_polish_bullet({
        bullet: debouncedBullet,
        role: debouncedPolishRole,
        tech_stack: debouncedPolishTechStack,
      });
      setAiResult({ success: true, data: result.data });
    } catch (e: any) {
      setAiResult({ success: false, error: e.message || 'Failed to polish bullet.' });
    } finally {
      setAiLoading(false);
    }
  }, [debouncedBullet, debouncedPolishRole, debouncedPolishTechStack]);

  const handleTailorResume = useCallback(async () => {
    setAiLoading(true);
    setAiResult(null);
    setAiToolSelected('tailor-resume');
    try {
      const result = await api_tailor_resume({
        resume_summary: resumeData.summary,
        resume_skills: resumeData.skills,
        resume_projects: resumeData.projects.map(p => ({ title: p.title, bullets: p.bullets.map(b => b.text).join('\n')})),
        job_description: jobDescription,
      });
      setAiResult({ success: true, data: result.data });
    } catch (e: any) {
      setAiResult({ success: false, error: e.message || 'Failed to tailor resume.' });
    } finally {
      setAiLoading(false);
    }
  }, [resumeData, jobDescription]);

  const handleGenerateSummary = useCallback(async () => {
    setAiLoading(true);
    setAiResult(null);
    setAiToolSelected('generate-summary');
    try {
      const result = await api_generate_summary({
        role: summaryRole,
        experience_level: summaryExperience,
        key_skills: summarySkills,
        target_company_type: summaryCompanyType,
      });
      setAiResult({ success: true, data: result.data });
    } catch (e: any) {
      setAiResult({ success: false, error: e.message || 'Failed to generate summary.' });
    } finally {
      setAiLoading(false);
    }
  }, [summaryRole, summaryExperience, summarySkills, summaryCompanyType]);

  // Trigger polish on debounced input change
  useEffect(() => {
    if (activeTab === 'ai-tools' && aiToolSelected === 'polish-bullet' && debouncedBullet.length > 3) {
      handlePolishBullet();
    }
  }, [debouncedBullet, debouncedPolishRole, debouncedPolishTechStack, activeTab, aiToolSelected, handlePolishBullet]);

  const allSkillsFormatted = useMemo(() => resumeData.skills.join(', '), [resumeData.skills]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-14 space-y-10 min-h-screen">
      {/* ── Header ── */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-1.5 bg-purple-500/10 text-purple-400 border border-purple-500/25 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider">
          <Wand2 className="w-3.5 h-3.5" aria-hidden="true" /> AI Resume Builder
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-white tracking-[-0.03em]">
          Your Resume, <span className="bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">Supercharged by AI</span>
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          Craft, polish, and tailor your professional resume with intelligent AI assistance for maximum impact.
        </p>
      </div>

      {/* ── Tabs ── */}
      <div className="flex flex-wrap justify-center gap-3 bg-[var(--surface-card)] p-2 rounded-xl border border-slate-800/70 shadow-lg">
        <button
          onClick={() => setActiveTab('input')}
          className={`active-press px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
            activeTab === 'input' ? 'bg-sky-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <User className="inline w-4 h-4 mr-2" aria-hidden="true" /> Your Data
        </button>
        <button
          onClick={() => setActiveTab('ai-tools')}
          className={`active-press px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
            activeTab === 'ai-tools' ? 'bg-purple-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <Lightbulb className="inline w-4 h-4 mr-2" aria-hidden="true" /> AI Tools
        </button>
        <button
          onClick={() => setActiveTab('preview')}
          className={`active-press px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
            activeTab === 'preview' ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <FileText className="inline w-4 h-4 mr-2" aria-hidden="true" /> Preview & Export
        </button>
      </div>

      {/* ── Content Area ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 py-4">
        {/* Main Content Pane */}
        <motion.div
          key={activeTab}
          initial="hidden"
          animate="visible"
          variants={sectionVariants}
          className="lg:col-span-2 space-y-6 craft-card p-6"
        >
          {activeTab === 'input' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2"><User className="w-5 h-5 text-sky-400" aria-hidden="true" /> Your Resume Data</h2>
              <div className="space-y-4">
                <label htmlFor="summary-input" className="text-xs font-bold uppercase text-slate-400">Professional Summary</label>
                <textarea
                  id="summary-input"
                  rows={4}
                  value={resumeData.summary}
                  onChange={(e) => setResumeData({ ...resumeData, summary: e.target.value })}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-sky-400 outline-none resize-y placeholder:text-slate-600"
                  placeholder="e.g., Results-driven software engineer..."
                />
              </div>

              {/* ── Experience ── */} 
              <div className="flex items-center justify-between mt-8 mb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2"><Briefcase className="w-5 h-5 text-emerald-400" aria-hidden="true" /> Experience</h3>
                <motion.button
                  onClick={addExperience}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="active-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" aria-hidden="true" /> Add Experience
                </motion.button>
              </div>
              <AnimatePresence mode="popLayout">
                {resumeData.experience.map((exp, expIdx) => (
                  <motion.div
                    key={exp.id}
                    initial={{ opacity: 0, y: -20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.95, transition: { duration: 0.2 } }}
                    transition={{ type: "spring", stiffness: 300, damping: 24 }}
                    className="craft-card p-4 space-y-3 relative"
                  >
                    <div className="flex items-center justify-between">
                      <input
                        type="text"
                        value={exp.title}
                        onChange={(e) => {
                          const newExp = [...resumeData.experience];
                          newExp[expIdx].title = e.target.value;
                          setResumeData({ ...resumeData, experience: newExp });
                        }}
                        className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:border-sky-400 outline-none placeholder:text-slate-600 mr-2"
                        placeholder="Job Title"
                      />
                      <motion.button
                        onClick={() => removeExperience(exp.id)}
                        whileHover={{ rotate: 90 }}
                        whileTap={{ scale: 0.9 }}
                        className="active-press p-1.5 rounded-full bg-rose-600 hover:bg-rose-500 text-white shrink-0 shadow-md"
                        aria-label="Remove experience entry"
                      >
                        <Minus className="w-4 h-4" aria-hidden="true" />
                      </motion.button>
                    </div>
                    <input
                      type="text"
                      value={exp.company}
                      onChange={(e) => {
                        const newExp = [...resumeData.experience];
                        newExp[expIdx].company = e.target.value;
                        setResumeData({ ...resumeData, experience: newExp });
                      }}
                      className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:border-sky-400 outline-none placeholder:text-slate-600"
                      placeholder="Company Name"
                    />
                    
                    <div className="space-y-2">
                      <label className="text-xs font-bold uppercase text-slate-400">Bullet Points (one per line)</label>
                      <AnimatePresence mode="popLayout">
                        {exp.bullets.map((bullet, bulletIdx) => (
                          <motion.div
                            key={bullet.id}
                            initial="hidden"
                            animate="visible"
                            exit="exit"
                            variants={bulletVariants}
                            className="flex items-center gap-2"
                          >
                            <textarea
                              rows={1}
                              value={bullet.text}
                              onChange={(e) => {
                                const newExp = [...resumeData.experience];
                                newExp[expIdx].bullets[bulletIdx].text = e.target.value;
                                setResumeData({ ...resumeData, experience: newExp });
                              }}
                              className="flex-1 bg-[var(--surface-input)] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:border-sky-400 outline-none resize-y placeholder:text-slate-600"
                              placeholder="Quantified achievement bullet"
                            />
                            <motion.button
                              onClick={() => setBulletToPolish(bullet.text)}
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.9 }}
                              className="active-press p-1.5 rounded-full bg-purple-600 hover:bg-purple-500 text-white shrink-0 shadow-md"
                              aria-label="Send bullet to AI polisher"
                            >
                              <Wand2 className="w-3.5 h-3.5" aria-hidden="true" />
                            </motion.button>
                            {exp.bullets.length > 1 && (
                              <motion.button
                                onClick={() => removeExpBullet(exp.id, bullet.id)}
                                whileHover={{ rotate: 90 }}
                                whileTap={{ scale: 0.9 }}
                                className="active-press p-1.5 rounded-full bg-rose-600 hover:bg-rose-500 text-white shrink-0 shadow-md"
                                aria-label="Remove bullet point"
                              >
                                <Minus className="w-3.5 h-3.5" aria-hidden="true" />
                              </motion.button>
                            )}
                          </motion.div>
                        ))}
                      </AnimatePresence>
                      <motion.button
                        onClick={() => addExpBullet(exp.id)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="active-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-md mt-2"
                      >
                        <Plus className="w-3.5 h-3.5" aria-hidden="true" /> Add Bullet
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* ── Skills ── */} 
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mt-8"><Code className="w-5 h-5 text-indigo-400" aria-hidden="true" /> Skills</h3>
              <textarea
                rows={2}
                value={resumeData.skills.join(', ')}
                onChange={(e) => setResumeData({ ...resumeData, skills: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
                className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-sky-400 outline-none resize-y placeholder:text-slate-600"
                placeholder="Comma-separated skills (e.g., React, Node.js, Python)"
              />
              
              {/* ── Projects ── */} 
              <div className="flex items-center justify-between mt-8 mb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2"><GraduationCap className="w-5 h-5 text-rose-400" aria-hidden="true" /> Projects</h3>
                <motion.button
                  onClick={addProject}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="active-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-md transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" aria-hidden="true" /> Add Project
                </motion.button>
              </div>
              <AnimatePresence mode="popLayout">
                {resumeData.projects.map((project, projectIdx) => (
                  <motion.div
                    key={project.id}
                    initial={{ opacity: 0, y: -20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.95, transition: { duration: 0.2 } }}
                    transition={{ type: "spring", stiffness: 300, damping: 24 }}
                    className="craft-card p-4 space-y-3 relative"
                  >
                    <div className="flex items-center justify-between">
                      <input
                        type="text"
                        value={project.title}
                        onChange={(e) => {
                          const newProjects = [...resumeData.projects];
                          newProjects[projectIdx].title = e.target.value;
                          setResumeData({ ...resumeData, projects: newProjects });
                        }}
                        className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:border-sky-400 outline-none placeholder:text-slate-600 mr-2"
                        placeholder="Project Title"
                      />
                      <motion.button
                        onClick={() => removeProject(project.id)}
                        whileHover={{ rotate: 90 }}
                        whileTap={{ scale: 0.9 }}
                        className="active-press p-1.5 rounded-full bg-rose-600 hover:bg-rose-500 text-white shrink-0 shadow-md"
                        aria-label="Remove project entry"
                      >
                        <Minus className="w-4 h-4" aria-hidden="true" />
                      </motion.button>
                    </div>
                    <textarea
                      rows={2}
                      value={project.description}
                      onChange={(e) => {
                        const newProjects = [...resumeData.projects];
                        newProjects[projectIdx].description = e.target.value;
                        setResumeData({ ...resumeData, projects: newProjects });
                      }}
                      className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:border-sky-400 outline-none resize-y placeholder:text-slate-600"
                      placeholder="Project Description"
                    />
                    
                    <div className="space-y-2">
                      <label className="text-xs font-bold uppercase text-slate-400">Bullet Points (one per line)</label>
                      <AnimatePresence mode="popLayout">
                        {project.bullets.map((bullet, bulletIdx) => (
                          <motion.div
                            key={bullet.id}
                            initial="hidden"
                            animate="visible"
                            exit="exit"
                            variants={bulletVariants}
                            className="flex items-center gap-2"
                          >
                            <textarea
                              rows={1}
                              value={bullet.text}
                              onChange={(e) => {
                                const newProjects = [...resumeData.projects];
                                newProjects[projectIdx].bullets[bulletIdx].text = e.target.value;
                                setResumeData({ ...resumeData, projects: newProjects });
                              }}
                              className="flex-1 bg-[var(--surface-input)] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:border-sky-400 outline-none resize-y placeholder:text-slate-600"
                              placeholder="Quantified achievement bullet"
                            />
                            <motion.button
                              onClick={() => setBulletToPolish(bullet.text)}
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.9 }}
                              className="active-press p-1.5 rounded-full bg-purple-600 hover:bg-purple-500 text-white shrink-0 shadow-md"
                              aria-label="Send bullet to AI polisher"
                            >
                              <Wand2 className="w-3.5 h-3.5" aria-hidden="true" />
                            </motion.button>
                            {project.bullets.length > 1 && (
                              <motion.button
                                onClick={() => removeProjBullet(project.id, bullet.id)}
                                whileHover={{ rotate: 90 }}
                                whileTap={{ scale: 0.9 }}
                                className="active-press p-1.5 rounded-full bg-rose-600 hover:bg-rose-500 text-white shrink-0 shadow-md"
                                aria-label="Remove bullet point"
                              >
                                <Minus className="w-3.5 h-3.5" aria-hidden="true" />
                              </motion.button>
                            )}
                          </motion.div>
                        ))}
                      </AnimatePresence>
                      <motion.button
                        onClick={() => addProjBullet(project.id)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="active-press flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-md mt-2"
                      >
                        <Plus className="w-3.5 h-3.5" aria-hidden="true" /> Add Bullet
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          {activeTab === 'ai-tools' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2"><Lightbulb className="w-5 h-5 text-purple-400" aria-hidden="true" /> AI Magic Tools</h2>
              
              {/* ── Generate Job Description ── */}
              <div className="craft-card p-5 space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2.5 text-emerald-300"><Briefcase className="w-5 h-5" aria-hidden="true" /> Generate Job Description</h3>
                <p className="text-xs text-slate-400">Create tailored job descriptions based on key criteria.</p>
                
                <label htmlFor="jd-title" className="text-xs font-bold uppercase text-slate-400">Job Title *</label>
                <input id="jd-title" type="text" value={jdTitle} onChange={(e) => setJdTitle(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., Senior Frontend Engineer" required
                />
                <label htmlFor="jd-company" className="text-xs font-bold uppercase text-slate-400">Company (Optional)</label>
                <input id="jd-company" type="text" value={jdCompany} onChange={(e) => setJdCompany(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., TechCorp Inc."
                />
                <label htmlFor="jd-experience" className="text-xs font-bold uppercase text-slate-400">Experience (Optional)</label>
                <input id="jd-experience" type="text" value={jdExperience} onChange={(e) => setJdExperience(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., 5+ years, Mid-level"
                />
                <label htmlFor="jd-location" className="text-xs font-bold uppercase text-slate-400">Location (Optional)</label>
                <input id="jd-location" type="text" value={jdLocation} onChange={(e) => setJdLocation(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., Remote / New York"
                />
                <label htmlFor="jd-work-mode" className="text-xs font-bold uppercase text-slate-400">Work Mode (Optional)</label>
                <input id="jd-work-mode" type="text" value={jdWorkMode} onChange={(e) => setJdWorkMode(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., Full-time, Contract"
                />
                <label htmlFor="jd-skills" className="text-xs font-bold uppercase text-slate-400">Key Skills (Optional)</label>
                <textarea id="jd-skills" rows={2} value={jdSkills} onChange={(e) => setJdSkills(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none resize-y placeholder:text-slate-600"
                  placeholder="e.g., React, TypeScript, GraphQL, AWS"
                />
                <label htmlFor="jd-notes" className="text-xs font-bold uppercase text-slate-400">Additional Notes (Optional)</label>
                <textarea id="jd-notes" rows={2} value={jdNotes} onChange={(e) => setJdNotes(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none resize-y placeholder:text-slate-600"
                  placeholder="e.g., Fast-paced startup, competitive salary, flexible hours"
                />
                
                <motion.button
                  onClick={handleGenerateJd}
                  disabled={aiLoading && aiToolSelected === 'generate-jd' || jdTitle.length < 3}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="active-press w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25 transition-all disabled:opacity-50"
                  style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)' }}
                >
                  {aiLoading && aiToolSelected === 'generate-jd' ? 
                    <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Generating...</> : 
                    <><Send className="w-4 h-4" aria-hidden="true" /> Generate JD →</>
                  }
                </motion.button>
                
                <AnimatePresence>
                  {aiResult?.data && aiToolSelected === 'generate-jd' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-emerald-950/30 text-emerald-300 border-emerald-500/25"
                    >
                      <strong>✨ Generated Job Description:</strong> <pre className="whitespace-pre-wrap font-sans text-emerald-200 mt-1">{(aiResult.data as string).replace(/\\n/g, '\n')}</pre>
                    </motion.div>
                  )}
                  {aiResult?.error && aiToolSelected === 'generate-jd' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-rose-950/30 text-rose-300 border-rose-500/25"
                    >
                      <strong>❌ Error:</strong> {aiResult.error}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Bullet Polisher */}
              <div className="craft-card p-5 space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2.5 text-purple-300"><Wand2 className="w-5 h-5" aria-hidden="true" /> Polish Bullet</h3>
                <p className="text-xs text-slate-400">Transform raw bullet points into quantified Google XYZ metrics.</p>
                
                <label htmlFor="polish-bullet-input" className="text-xs font-bold uppercase text-slate-400">Raw Bullet Point</label>
                <textarea
                  id="polish-bullet-input"
                  rows={2}
                  value={bulletToPolish}
                  onChange={(e) => setBulletToPolish(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-purple-400 outline-none resize-y placeholder:text-slate-600"
                  placeholder="e.g., Managed backend development"
                />
                
                <label htmlFor="polish-role" className="text-xs font-bold uppercase text-slate-400">Target Role (Optional)</label>
                <input
                  id="polish-role"
                  type="text"
                  value={polishRole}
                  onChange={(e) => setPolishRole(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-purple-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., Senior Software Engineer"
                />
                
                <label htmlFor="polish-tech-stack" className="text-xs font-bold uppercase text-slate-400">Tech Stack (Optional)</label>
                <input
                  id="polish-tech-stack"
                  type="text"
                  value={polishTechStack}
                  onChange={(e) => setPolishTechStack(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-purple-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., Node.js, React, AWS"
                />
                
                <motion.button
                  onClick={handlePolishBullet}
                  disabled={aiLoading && aiToolSelected === 'polish-bullet' || bulletToPolish.length < 5}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="active-press w-full bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-400 hover:to-indigo-400 text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-purple-500/25 transition-all disabled:opacity-50"
                  style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)' }}
                >
                  {aiLoading && aiToolSelected === 'polish-bullet' ? 
                    <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Polishing...</> : 
                    <><Wand2 className="w-4 h-4" aria-hidden="true" /> Polish Bullet →</>
                  }
                </motion.button>
                
                <AnimatePresence>
                  {aiResult?.data && aiToolSelected === 'polish-bullet' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-purple-950/30 text-purple-300 border-purple-500/25"
                    >
                      <strong>✨ Polished Bullet:</strong> <pre className="whitespace-pre-wrap font-sans text-purple-200 mt-1">{(aiResult.data as string).replace(/\\n/g, '\n')}</pre>
                    </motion.div>
                  )}
                  {aiResult?.error && aiToolSelected === 'polish-bullet' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-rose-950/30 text-rose-300 border-rose-500/25"
                    >
                      <strong>❌ Error:</strong> {aiResult.error}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Tailor Resume */}
              <div className="craft-card p-5 space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2.5 text-sky-300"><FileText className="w-5 h-5" aria-hidden="true" /> Tailor Resume to JD</h3>
                <p className="text-xs text-slate-400">Analyze your resume against a target job description to highlight keywords and optimize content.</p>
                
                <label htmlFor="jd-textarea" className="text-xs font-bold uppercase text-slate-400">Target Job Description</label>
                <textarea
                  id="jd-textarea"
                  rows={6}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-sky-400 outline-none resize-y placeholder:text-slate-600"
                  placeholder="Paste the full job description here..."
                />
                
                <motion.button
                  onClick={handleTailorResume}
                  disabled={aiLoading && aiToolSelected === 'tailor-resume' || jobDescription.length < 20 || resumeData.summary.length < 10}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="active-press w-full bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-sky-500/25 transition-all disabled:opacity-50"
                  style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)' }}
                >
                  {aiLoading && aiToolSelected === 'tailor-resume' ? 
                    <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Tailoring...</> : 
                    <><FileText className="w-4 h-4" aria-hidden="true" /> Tailor Resume →</>
                  }
                </motion.button>
                
                <AnimatePresence>
                  {aiResult?.data && aiToolSelected === 'tailor-resume' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-sky-950/30 text-sky-300 border-sky-500/25"
                    >
                      <strong>✨ Tailoring Analysis:</strong> <pre className="whitespace-pre-wrap font-sans text-sky-200 mt-1">{(aiResult.data as string).replace(/\\n/g, '\n')}</pre>
                    </motion.div>
                  )}
                  {aiResult?.error && aiToolSelected === 'tailor-resume' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-rose-950/30 text-rose-300 border-rose-500/25"
                    >
                      <strong>❌ Error:</strong> {aiResult.error}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Generate Summary */}
              <div className="craft-card p-5 space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2.5 text-emerald-300"><User className="w-5 h-5" aria-hidden="true" /> Generate Summary</h3>
                <p className="text-xs text-slate-400">Get 3 professional summary options tailored to your target role.</p>
                
                <label htmlFor="summary-role" className="text-xs font-bold uppercase text-slate-400">Target Role</label>
                <input id="summary-role" type="text" value={summaryRole} onChange={(e) => setSummaryRole(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., Full-Stack Developer"
                />

                <label htmlFor="summary-experience" className="text-xs font-bold uppercase text-slate-400">Experience Level</label>
                <input id="summary-experience" type="text" value={summaryExperience} onChange={(e) => setSummaryExperience(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., 5 years, Senior, Fresher"
                />

                <label htmlFor="summary-skills" className="text-xs font-bold uppercase text-slate-400">Key Skills (comma-separated)</label>
                <input id="summary-skills" type="text" value={summarySkills} onChange={(e) => setSummarySkills(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., React, Node.js, AWS, Python"
                />

                <label htmlFor="summary-company-type" className="text-xs font-bold uppercase text-slate-400">Target Company Type</label>
                <input id="summary-company-type" type="text" value={summaryCompanyType} onChange={(e) => setSummaryCompanyType(e.target.value)}
                  className="w-full bg-[var(--surface-input)] border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:border-emerald-400 outline-none placeholder:text-slate-600"
                  placeholder="e.g., Product Startup, FAANG, Service-based"
                />
                
                <motion.button
                  onClick={handleGenerateSummary}
                  disabled={aiLoading && aiToolSelected === 'generate-summary' || summaryRole.length < 3}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="active-press w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25 transition-all disabled:opacity-50"
                  style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)' }}
                >
                  {aiLoading && aiToolSelected === 'generate-summary' ? 
                    <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Generating...</> : 
                    <><Send className="w-4 h-4" aria-hidden="true" /> Generate Summary →</>
                  }
                </motion.button>

                <AnimatePresence>
                  {aiResult?.data && aiToolSelected === 'generate-summary' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-emerald-950/30 text-emerald-300 border-emerald-500/25"
                    >
                      <strong>✨ AI-Generated Summaries:</strong> <pre className="whitespace-pre-wrap font-sans text-emerald-200 mt-1">{(aiResult.data as string).replace(/\\n/g, '\n')}</pre>
                    </motion.div>
                  )}
                  {aiResult?.error && aiToolSelected === 'generate-summary' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="p-4 rounded-xl text-xs leading-relaxed border bg-rose-950/30 text-rose-300 border-rose-500/25"
                    >
                      <strong>❌ Error:</strong> {aiResult.error}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          )}

          {activeTab === 'preview' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2"><FileText className="w-5 h-5 text-emerald-400" aria-hidden="true" /> Resume Preview</h2>
              <div className="craft-card p-6 min-h-[500px] font-sans text-sm text-slate-200 leading-relaxed overflow-x-auto">
                {/* Resume Header */}
                <div className="mb-6 pb-4 border-b border-slate-700/50">
                  <h3 className="text-2xl font-bold text-white mb-1">[Your Name]</h3>
                  <p className="text-sm text-sky-400">{resumeData.summary || '[Professional Summary]'}</p>
                </div>
                
                {/* Summary */}
                {resumeData.summary && (
                  <div className="mb-6">
                    <h4 className="text-lg font-bold text-indigo-400 mb-2">Summary</h4>
                    <p className="text-slate-300">{resumeData.summary}</p>
                  </div>
                )}

                {/* Experience */}
                {resumeData.experience.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-lg font-bold text-emerald-400 mb-2">Experience</h4>
                    {resumeData.experience.map((exp, idx) => (
                      <div key={exp.id} className="mb-4 last:mb-0">
                        <p className="font-semibold text-white">{exp.title} at {exp.company}</p>
                        <ul className="list-disc list-outside ml-5 text-slate-300">
                          <AnimatePresence>
                            {exp.bullets.map((bullet) => (
                              <motion.li
                                key={bullet.id}
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 5 }}
                                transition={{ duration: 0.15 }}
                                className="mb-1 last:mb-0"
                              >
                                {bullet.text}
                              </motion.li>
                            ))}
                          </AnimatePresence>
                        </ul>
                      </div>
                    ))}
                  </div>
                )}

                {/* Skills */}
                {resumeData.skills.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-lg font-bold text-sky-400 mb-2">Skills</h4>
                    <p className="flex flex-wrap gap-2">
                      {resumeData.skills.map((skill, idx) => (
                        <span key={idx} className="bg-sky-500/15 text-sky-300 text-xs font-mono px-3 py-1 rounded-full">
                          {skill}
                        </span>
                      ))}
                    </p>
                  </div>
                )}

                {/* Projects */}
                {resumeData.projects.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-lg font-bold text-rose-400 mb-2">Projects</h4>
                    {resumeData.projects.map((project, idx) => (
                      <div key={project.id} className="mb-4 last:mb-0">
                        <p className="font-semibold text-white">{project.title}</p>
                        <p className="text-slate-300 italic mb-1">{project.description}</p>
                        <ul className="list-disc list-outside ml-5 text-slate-300">
                          <AnimatePresence>
                            {project.bullets.map((bullet) => (
                              <motion.li
                                key={bullet.id}
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 5 }}
                                transition={{ duration: 0.15 }}
                                className="mb-1 last:mb-0"
                              >
                                {bullet.text}
                              </motion.li>
                            ))}
                          </AnimatePresence>
                        </ul>
                      </div>
                    ))}
                  </div>
                )}

                {resumeData.summary.length === 0 && resumeData.experience.length === 0 && resumeData.skills.length === 0 && resumeData.projects.length === 0 && (
                  <div className="text-center text-slate-500 py-10">No resume data to display. Start by entering your information.</div>
                )}
              </div>
            </div>
          )}
        </motion.div>

        {/* Right Sidebar for AI Results / Actions */}
        <motion.div
          key={activeTab + '-sidebar'}
          initial="hidden"
          animate="visible"
          variants={sectionVariants}
          className="lg:col-span-1 space-y-6 craft-card p-6"
        >
          <h2 className="text-xl font-bold text-white flex items-center gap-2"><Sparkles className="w-5 h-5 text-purple-400" aria-hidden="true" /> AI Insights & Actions</h2>
          <div className="space-y-4 text-sm text-slate-300">
            <p>Select an AI tool from the 'AI Tools' tab on the left to see suggestions here.</p>
            <p className="text-xs text-slate-500">Use the AI tools to refine your resume content and apply for jobs with confidence.</p>
          </div>
          {/* Display general AI results here too */}
          <AnimatePresence mode="wait">
            {aiResult && !aiLoading && (
              <motion.div
                key="general-ai-result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className={`p-4 rounded-xl text-xs leading-relaxed border ${aiResult.success ? 'bg-emerald-950/30 text-emerald-300 border-emerald-500/25' : 'bg-rose-950/30 text-rose-300 border-rose-500/25'}`}
              >
                <strong>{aiResult.success ? '✅ Success:' : '❌ Error:'}</strong>
                <pre className="whitespace-pre-wrap font-sans mt-1">
                  {aiResult.data ? aiResult.data.replace(/\\n/g, '\n') : aiResult.error}
                </pre>
              </motion.div>
            )}
          </AnimatePresence>
          {aiLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-4 rounded-xl text-xs leading-relaxed border bg-sky-950/30 text-sky-300 border-sky-500/25 flex items-center justify-center gap-2"
            >
              <Loader2 className="w-4 h-4 animate-spin text-sky-400" aria-hidden="true" />
              <span>Loading AI response...</span>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
