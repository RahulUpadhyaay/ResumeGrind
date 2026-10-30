import React from 'react';
import { Globe, ExternalLink, Code2, Layout } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ProjectPreview({ context }) {
  if (!context || context.type !== 'live_project') return null;

  const { title, project_url, description, technologies } = context;

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="h-full flex flex-col bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center space-x-3 overflow-hidden">
          <Globe className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <div className="truncate">
            <h4 className="text-sm font-medium text-white truncate">{title || 'Live Project'}</h4>
            <a href={project_url} target="_blank" rel="noopener noreferrer" className="text-xs text-teal-400 hover:text-teal-300 hover:underline flex items-center mt-0.5 truncate">
              {project_url}
            </a>
          </div>
        </div>
        
        <a 
          href={project_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors flex-shrink-0 flex items-center space-x-2 border border-slate-700"
        >
          <span className="text-xs font-medium">Open</span>
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>

      {/* Content Area - Split between details and iframe attempt */}
      <div className="flex-1 overflow-y-auto scrollbar-custom p-6 space-y-6">
        
        {/* Project Details Card */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <h5 className="text-slate-300 font-medium mb-3 flex items-center">
            <Layout className="w-4 h-4 mr-2" /> Project Details
          </h5>
          <p className="text-sm text-slate-400 leading-relaxed mb-4">
            {description || 'This live project is being analyzed for the interview.'}
          </p>
          
          {technologies && technologies.length > 0 && (
            <div>
              <h6 className="text-xs text-slate-500 uppercase tracking-wider mb-2 flex items-center">
                <Code2 className="w-3 h-3 mr-1" /> Tech Stack
              </h6>
              <div className="flex flex-wrap gap-2">
                {technologies.map((tech, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-md text-xs bg-slate-950 border border-slate-700 text-slate-300 shadow-sm">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Live Preview Iframe (with sandboxing for safety, may not load if X-Frame-Options is set) */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden h-[400px] flex flex-col relative">
          <div className="bg-slate-800 px-3 py-2 text-xs text-slate-400 border-b border-slate-700 flex justify-between">
            <span>Live Preview</span>
            <span className="text-slate-500">May be blocked by site settings</span>
          </div>
          <iframe 
            src={project_url} 
            className="w-full flex-1 bg-white"
            sandbox="allow-scripts allow-same-origin"
            title="Project Preview"
            loading="lazy"
          />
        </div>

      </div>
      
      {/* Footer */}
      <div className="p-3 bg-slate-950 border-t border-slate-800 text-xs text-slate-500 text-center">
        The AI is referencing this deployed application.
      </div>
    </motion.div>
  );
}
