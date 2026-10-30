import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[300px] flex flex-col items-center justify-center p-6 bg-slate-900/90 border border-amber-500/30 rounded-2xl text-center max-w-lg mx-auto shadow-2xl my-8">
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center mb-4 text-amber-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Display Notice</h3>
          <p className="text-xs text-slate-300 mb-4 max-w-sm leading-relaxed">
            A temporary component display issue occurred. Your interview progress and responses are safely preserved.
          </p>
          <button
            onClick={this.handleReset}
            className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md shadow-emerald-500/20"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh View</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
