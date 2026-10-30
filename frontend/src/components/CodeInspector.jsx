import React, { useState } from 'react';
import { Github, ExternalLink, FileCode2, Copy, Check, Play, Terminal, Code2, Sparkles, RefreshCw, ShieldAlert, CheckCircle2, XCircle, RotateCcw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { executeCode } from '../api/client';

const LANGUAGE_TEMPLATES = {
  python: `# LeetCode 1: Two Sum
# Constraints: 2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9, -10^9 <= target <= 10^9

class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        # Implement your O(N) logic here:
        seen = {}
        for i, num in enumerate(nums):
            diff = target - num
            if diff in seen:
                return [seen[diff], i]
            seen[num] = i
        return []
`,
  javascript: `// LeetCode 1: Two Sum
// Constraints: 2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9, -10^9 <= target <= 10^9

var twoSum = function(nums, target) {
    // Implement your O(N) logic here:
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {
        const diff = target - nums[i];
        if (map.has(diff)) {
            return [map.get(diff), i];
        }
        map.set(nums[i], i);
    }
    return [];
};
`,
  java: `// LeetCode 1: Two Sum
// Constraints: 2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9, -10^9 <= target <= 10^9

import java.util.*;

class Solution {
    public int[] twoSum(int[] nums, int target) {
        // Implement your O(N) logic here:
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[]{map.get(complement), i};
            }
            map.put(nums[i], i);
        }
        return new int[0];
    }
}
`,
  cpp: `// LeetCode 1: Two Sum
// Constraints: 2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9, -10^9 <= target <= 10^9

#include <vector>
#include <unordered_map>
using namespace std;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Implement your O(N) logic here:
        unordered_map<int, int> seen;
        for (int i = 0; i < nums.size(); i++) {
            int diff = target - nums[i];
            if (seen.find(diff) != seen.end()) {
                return {seen[diff], i};
            }
            seen[nums[i]] = i;
        }
        return {};
    }
};
`
};

export default function CodeInspector({ context }) {
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState('sandbox');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);

  const initialLang = (context?.language || 'python').toLowerCase();
  const normalizedLang = initialLang === 'js' ? 'javascript' : (initialLang === 'c++' ? 'cpp' : (['python', 'javascript', 'java', 'cpp'].includes(initialLang) ? initialLang : 'python'));
  const [selectedLanguage, setSelectedLanguage] = useState(normalizedLang);

  if (!context || context.type !== 'github_code') return null;

  const repoName = context.repo_name || (context.context_title ? context.context_title.replace('GitHub: ', '').split(' / ')[0] : 'Repository');
  const cleanPath = context.file_path || (selectedLanguage === 'python' ? 'solution.py' : selectedLanguage === 'javascript' ? 'solution.js' : selectedLanguage === 'java' ? 'Solution.java' : 'solution.cpp');
  const codeSnippet = context.code_snippet || LANGUAGE_TEMPLATES[selectedLanguage] || LANGUAGE_TEMPLATES.python;
  const highlightLines = context.highlight_lines || [1, 2, 3];
  const githubUrl = context.github_url || `https://github.com/${repoName}`;

  const [sandboxCode, setSandboxCode] = useState(codeSnippet);
  const lines = codeSnippet.split('\n');

  const handleLanguageChange = (newLang) => {
    setSelectedLanguage(newLang);
    if (LANGUAGE_TEMPLATES[newLang]) {
      setSandboxCode(LANGUAGE_TEMPLATES[newLang]);
    }
  };

  const handleResetTemplate = () => {
    if (LANGUAGE_TEMPLATES[selectedLanguage]) {
      setSandboxCode(LANGUAGE_TEMPLATES[selectedLanguage]);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(mode === 'sandbox' ? sandboxCode : codeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunCode = async () => {
    setIsExecuting(true);
    setExecutionResult(null);
    try {
      const res = await executeCode(sandboxCode, selectedLanguage);
      setExecutionResult(res);
    } catch (err) {
      setExecutionResult({
        stdout: '',
        stderr: err.response?.data?.detail || err.message || 'Execution failed',
        execution_time_ms: 0,
        exit_code: 1,
        status: 'error'
      });
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="h-full flex flex-col bg-slate-900/90 border border-slate-700/80 rounded-2xl overflow-hidden shadow-2xl"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between p-3.5 border-b border-slate-700/80 bg-slate-800/80 backdrop-blur gap-2">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="p-2 rounded-lg bg-slate-700/80 border border-slate-600 flex-shrink-0">
            <Github className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="truncate">
            <h4 className="text-xs font-semibold text-white truncate">{repoName}</h4>
            <div className="flex items-center text-[11px] text-slate-300 mt-0.5">
              <FileCode2 className="w-3 h-3 mr-1 text-emerald-400" />
              <span className="truncate font-mono">{cleanPath}</span>
            </div>
          </div>
        </div>

        {/* Action Controls & Language Selector */}
        <div className="flex items-center space-x-2 flex-wrap">
          {mode === 'sandbox' && (
            <div className="flex items-center space-x-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <select
                value={selectedLanguage}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="bg-transparent text-cyan-300 font-mono text-xs font-semibold px-2 py-0.5 focus:outline-none cursor-pointer"
                title="Select Programming Language"
              >
                <option value="python" className="bg-slate-900 text-white">Python 3</option>
                <option value="javascript" className="bg-slate-900 text-white">JavaScript</option>
                <option value="java" className="bg-slate-900 text-white">Java 21</option>
                <option value="cpp" className="bg-slate-900 text-white">C++ (g++)</option>
              </select>

              <button
                onClick={handleResetTemplate}
                className="p-1 text-slate-400 hover:text-cyan-300 transition-colors"
                title="Reset to pure function template"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Mode Switcher Tabs */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setMode('viewer')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                mode === 'viewer' 
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sparkles className="w-3 h-3" />
              <span className="hidden sm:inline">Viewer</span>
            </button>
            <button
              onClick={() => setMode('sandbox')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                mode === 'sandbox' 
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Code2 className="w-3 h-3" />
              <span>IDE</span>
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1.5 bg-slate-700/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-600 rounded-lg text-xs transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {mode === 'sandbox' ? (
            <button
              onClick={handleRunCode}
              disabled={isExecuting}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold border border-emerald-400 rounded-lg text-xs transition-all shadow-lg shadow-emerald-500/20"
            >
              {isExecuting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>{isExecuting ? 'Running...' : 'Run Code'}</span>
            </button>
          ) : (
            githubUrl && (
              <a 
                href={githubUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium border border-slate-600 rounded-lg text-xs transition-colors"
              >
                <span>GitHub</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )
          )}
        </div>
      </div>

      {/* Main Area: Viewer or Live Monaco Sandbox */}
      <div className="flex-1 flex flex-col min-h-0 bg-[#18202f]">
        {mode === 'viewer' ? (
          <div className="flex-1 overflow-auto p-4 font-mono text-xs leading-relaxed scrollbar-custom">
            <table className="w-full border-collapse">
              <tbody>
                {lines.map((line, idx) => {
                  const lineNum = idx + 1;
                  const isHighlighted = highlightLines.includes(lineNum);
                  return (
                    <tr 
                      key={idx}
                      className={`transition-colors ${
                        isHighlighted 
                          ? 'bg-emerald-500/15 border-l-2 border-emerald-400' 
                          : 'hover:bg-slate-800/40 border-l-2 border-transparent'
                      }`}
                    >
                      <td className="w-10 pr-3 py-0.5 text-right select-none text-slate-500 text-[11px] font-mono">
                        {lineNum}
                      </td>
                      <td className={`pl-2 py-0.5 font-mono whitespace-pre ${
                        isHighlighted ? 'text-emerald-200 font-semibold' : 'text-slate-200'
                      }`}>
                        {line || ' '}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex-1 flex flex-col p-2 min-h-0 relative">
            <textarea
              value={sandboxCode}
              onChange={(e) => setSandboxCode(e.target.value)}
              className="w-full flex-1 bg-slate-950 text-emerald-300 font-mono text-xs p-4 rounded-xl border border-slate-800 focus:border-cyan-500 focus:outline-none resize-none leading-relaxed scrollbar-custom"
              placeholder="// Type your code solution here..."
              spellCheck="false"
            />
          </div>
        )}

        {/* Execution Output Drawer */}
        <AnimatePresence>
          {executionResult && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-slate-700 bg-slate-950 p-4 text-xs font-mono max-h-56 overflow-auto border-cyan-500/30"
            >
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-slate-800">
                <span className="flex items-center gap-1.5 font-bold text-cyan-400">
                  <Terminal className="w-4 h-4" />
                  Terminal Output
                </span>
                <div className="flex items-center gap-2">
                  {executionResult.status === 'security_violation' && (
                    <span className="text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded border border-red-500/30 flex items-center gap-1 font-semibold">
                      <ShieldAlert className="w-3 h-3" />
                      AST Sandbox Blocked
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400">
                    Time: {executionResult.execution_time_ms}ms | Status: {executionResult.status}
                  </span>
                </div>
              </div>
              
              {/* Test Cases Results if any */}
              {executionResult.test_results && executionResult.test_results.length > 0 && (
                <div className="mb-3 space-y-1.5 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Automated Unit Test Results:</div>
                  {executionResult.test_results.map((tr, idx) => (
                    <div key={idx} className="flex items-center justify-between text-[11px]">
                      <span className="flex items-center gap-1.5 text-slate-300">
                        {tr.passed ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-red-400" />
                        )}
                        {tr.name}
                      </span>
                      <span className={tr.passed ? "text-emerald-400 font-semibold" : "text-red-400 font-semibold"}>
                        {tr.passed ? "PASSED" : "FAILED"}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {executionResult.stdout && (
                <div className="text-emerald-400 whitespace-pre-wrap mb-1">{executionResult.stdout}</div>
              )}
              {executionResult.stderr && (
                <div className="text-red-400 whitespace-pre-wrap mb-1">{executionResult.stderr}</div>
              )}

              {/* AI Code Reviewer Box */}
              {executionResult.ai_review && (
                <div className="mt-3 p-3 rounded-xl bg-slate-900 border border-emerald-500/30 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-400 mb-1 text-[11px] uppercase tracking-wider">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>AI Interviewer Code Review</span>
                  </div>
                  <p className="text-slate-200 leading-relaxed font-sans">{executionResult.ai_review}</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer Banner */}
      <div className="px-4 py-2 bg-slate-800/90 border-t border-slate-700/80 text-xs text-slate-300 flex justify-between items-center">
        <span className="flex items-center gap-1.5 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          {mode === 'viewer' ? 'Highlighted lines referenced in question' : 'LeetCode Auto-Test Harness Active'}
        </span>
        <span className="uppercase text-[10px] font-mono text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
          {selectedLanguage}
        </span>
      </div>
    </motion.div>
  );
}
