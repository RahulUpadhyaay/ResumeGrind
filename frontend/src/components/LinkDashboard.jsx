import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Github, Globe, Linkedin, ArrowRight, CheckCircle2, ExternalLink, Loader2 } from 'lucide-react';
import { inspectLinks } from '../api/client';

/**
 * LinkDashboard Component
 * 
 * WHY: After parsing the resume, we show the candidate all discovered links
 * and their crawling status. This provides visual feedback during the async
 * inspection process and builds excitement for the interview.
 * 
 * The component:
 * 1. Receives extractedUrls (objects with {url, url_type}) from resume parsing
 * 2. Automatically triggers concurrent link inspection via the backend
 * 3. Displays crawl progress and results (languages, file counts, etc.)
 * 4. Enables the "Start Interview" button once inspection is complete
 */
export default function LinkDashboard({ resumeAnalysis, onInspectionComplete }) {
  const [isInspecting, setIsInspecting] = useState(true);
  const [inspectionResult, setInspectionResult] = useState(null);

  // WHY: extracted_urls is an array of { url, url_type } objects from the backend
  const urls = resumeAnalysis?.extracted_urls || [];

  useEffect(() => {
    const runInspection = async () => {
      if (urls.length === 0) {
        setIsInspecting(false);
        setInspectionResult({ github_repos: [], portfolio_data: [], linkedin_data: null });
        return;
      }

      try {
        // WHY: inspectLinks sends the full URL objects to the backend,
        // which uses url_type to determine how to crawl each link
        const result = await inspectLinks(urls);
        setInspectionResult(result);
      } catch (error) {
        console.error("Inspection failed:", error);
        // WHY: Fail gracefully — if crawling fails, we can still do a
        // general interview based on resume text and skills
        setInspectionResult({ github_repos: [], portfolio_data: [], linkedin_data: null });
      } finally {
        setIsInspecting(false);
      }
    };

    runInspection();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleContinue = () => {
    onInspectionComplete(inspectionResult);
  };

  // WHY: Determine icon and display info based on url_type from the backend
  const getUrlDisplay = (urlObj) => {
    const urlStr = urlObj.url;
    const urlType = urlObj.url_type;

    let Icon = Globe;
    let title = urlStr;
    let type = 'portfolio';
    let repoData = null;
    let portfolioData = null;

    if (urlType === 'github_repo' || urlType === 'github_profile') {
      type = 'github';
      Icon = Github;
      // Extract readable repo name from URL
      const parts = urlStr.split('github.com/')[1]?.split('/') || [];
      title = parts.length > 1 ? `${parts[0]}/${parts[1]}` : parts[0] || urlStr;

      // Match with inspection results by repo name
      if (!isInspecting && inspectionResult) {
        repoData = inspectionResult.github_repos?.find(
          r => urlStr.includes(`${r.owner}/${r.repo_name}`) || urlStr.includes(r.owner)
        );
      }
    } else if (urlType === 'linkedin') {
      type = 'linkedin';
      Icon = Linkedin;
      const username = urlStr.split('linkedin.com/in/')[1]?.split(/[/?]/)[0] || urlStr;
      title = `LinkedIn: ${username}`;
    } else {
      type = 'portfolio';
      Icon = Globe;
      if (!isInspecting && inspectionResult) {
        portfolioData = inspectionResult.portfolio_data?.find(p => p.url === urlStr);
      }
    }

    return { Icon, title, type, repoData, portfolioData, urlStr };
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  return (
    <div className="max-w-4xl mx-auto w-full p-6">
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-bold text-white mb-4">Digital Footprint Discovered</h2>
        <p className="text-slate-400">
          We found <span className="text-emerald-400 font-semibold">{urls.length}</span> links in your resume.
          {isInspecting
            ? " Inspecting them to craft highly contextual questions..."
            : " Inspection complete — ready for your interview!"}
        </p>
      </div>

      {urls.length === 0 ? (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-8 text-center mb-8">
          <p className="text-slate-400 mb-4">No external links found in your resume.</p>
          <p className="text-sm text-slate-500">
            We'll conduct a standard technical interview based on your listed skills and experience.
          </p>
        </div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid gap-6 md:grid-cols-2 mb-10"
        >
          {urls.map((urlObj, i) => {
            const { Icon, title, type, repoData, portfolioData, urlStr } = getUrlDisplay(urlObj);

            return (
              <motion.div
                key={i}
                variants={itemVariants}
                className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 hover:border-slate-500 transition-colors"
              >
                {/* URL Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-700">
                      <Icon className="w-5 h-5 text-slate-300" />
                    </div>
                    <div className="truncate">
                      <h4 className="font-medium text-white truncate">{title}</h4>
                      <a
                        href={urlStr}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-teal-400 hover:text-teal-300 hover:underline flex items-center mt-1"
                      >
                        <span className="truncate max-w-[200px]">{urlStr}</span>
                        <ExternalLink className="w-3 h-3 ml-1 flex-shrink-0" />
                      </a>
                    </div>
                  </div>
                  {isInspecting ? (
                    <Loader2 className="w-5 h-5 text-emerald-500 animate-spin flex-shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  )}
                </div>

                {/* GitHub Repo Details */}
                {!isInspecting && repoData && type === 'github' && (
                  <div className="mt-4 pt-4 border-t border-slate-700 text-sm">
                    {repoData.description && (
                      <p className="text-slate-400 text-xs mb-3 line-clamp-2">{repoData.description}</p>
                    )}
                    <div className="flex flex-wrap gap-2 mb-2">
                      {Object.keys(repoData.languages || {}).map(lang => (
                        <span
                          key={lang}
                          className="px-2 py-0.5 rounded text-xs bg-slate-900 border border-slate-700 text-slate-300"
                        >
                          {lang}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-500">
                      <span>⭐ {repoData.stars || 0}</span>
                      <span>📁 {repoData.key_files?.length || 0} key files indexed</span>
                    </div>
                  </div>
                )}

                {/* Portfolio Details */}
                {!isInspecting && portfolioData && type === 'portfolio' && (
                  <div className="mt-4 pt-4 border-t border-slate-700 text-sm">
                    <p className="text-slate-300 line-clamp-2 text-xs mb-2">
                      {portfolioData.description || portfolioData.title || 'Live website detected'}
                    </p>
                  </div>
                )}

                {/* LinkedIn placeholder */}
                {!isInspecting && type === 'linkedin' && (
                  <div className="mt-4 pt-4 border-t border-slate-700 text-sm">
                    <p className="text-slate-400 text-xs">
                      LinkedIn profile detected. Interview questions will reference your professional experience.
                    </p>
                  </div>
                )}
              </motion.div>
            );
          })}
        </motion.div>
      )}

      {/* Start Interview Button */}
      <div className="flex justify-center">
        <button
          onClick={handleContinue}
          disabled={isInspecting}
          className={`flex items-center space-x-2 px-8 py-4 rounded-xl font-semibold text-lg transition-all ${
            isInspecting
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-emerald-500 text-slate-950 hover:bg-emerald-400 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] shadow-lg hover:-translate-y-1'
          }`}
        >
          <span>{isInspecting ? 'Inspecting Links...' : 'Start Interview'}</span>
          {!isInspecting && <ArrowRight className="w-5 h-5" />}
        </button>
      </div>
    </div>
  );
}
