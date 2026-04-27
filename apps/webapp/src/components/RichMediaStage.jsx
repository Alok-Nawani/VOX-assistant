import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image as ImageIcon, Code, FileText, Download, ExternalLink, Copy } from 'lucide-react';

const RichMediaStage = ({ activeMedia }) => {
  if (!activeMedia) {
    return (
      <div className="empty-stage">
        <div className="stage-placeholder">
          <div className="placeholder-icon"><FileText size={48} /></div>
          <h3>VIRTUAL_STAGE_IDLE</h3>
          <p>Requested visual assets and complex data structures will be projected here for enhanced analysis.</p>
        </div>
      </div>
    );
  }

  const { type, content, title, image_url, prompt, language } = activeMedia;

  return (
    <div className="rich-media-stage">
      <AnimatePresence mode="wait">
        <motion.div
          key={image_url || content || 'stage'}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 1.05 }}
          className="stage-content-wrapper"
        >
          <div className="stage-header">
            <div className="stage-title">
              {type === 'image_generation' && <><ImageIcon size={18} /> SYNTHESIZED_IMAGE</>}
              {type === 'code_solution' && <><Code size={18} /> CODE_ARCHITECTURE</>}
              {type === 'poem_story' && <><FileText size={18} /> LITERARY_CONSTRUCT</>}
            </div>
            <div className="stage-actions">
              {type === 'image_generation' && (
                <>
                  <button onClick={() => window.open(image_url, '_blank')}><ExternalLink size={16} /></button>
                  <a href={image_url} download><Download size={16} /></a>
                </>
              )}
              {type === 'code_solution' && (
                <button onClick={() => navigator.clipboard.writeText(content)}><Copy size={16} /></button>
              )}
            </div>
          </div>

          <div className="stage-body">
            {type === 'image_generation' && (
              <div className="stage-image-container">
                <img src={image_url} alt={prompt} className="stage-image" />
                <div className="stage-caption">PROMPT: {prompt}</div>
              </div>
            )}

            {type === 'code_solution' && (
              <pre className="stage-code">
                <div className="code-lang-badge">{language || 'CODE'}</div>
                <code>{content.replace(/```[a-z]*\n|```/g, '')}</code>
              </pre>
            )}

            {type === 'poem_story' && (
              <div className="stage-text">
                {content.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default RichMediaStage;
