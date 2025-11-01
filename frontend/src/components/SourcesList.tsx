import React, { useState } from 'react';
import { PDFViewer } from './PDFViewer';

interface Source {
  law_name: string;
  article_num: string;
  domain_id: string;
}

interface SourcesListProps {
  sources: Source[];
}

export const SourcesList: React.FC<SourcesListProps> = ({ sources }) => {
  const [selectedArticle, setSelectedArticle] = useState<{
    domainId: string;
    articleNum: string;
  } | null>(null);

  const handleArticleClick = (domainId: string, articleNum: string) => {
    setSelectedArticle({ domainId, articleNum });
  };

  return (
    <>
      <div className="sources-list">
        <h3>📚 Nguồn tham khảo:</h3>
        
        {sources.map((source, idx) => (
          <div key={idx} className="source-item">
            <strong>{idx + 1}. {source.law_name}</strong>
            <button
              onClick={() => handleArticleClick(source.domain_id, source.article_num)}
              className="view-pdf-btn"
            >
              📄 Xem Điều {source.article_num}
            </button>
          </div>
        ))}
        
        <p className="hint">💡 Click vào nút để xem tài liệu gốc với highlight</p>
      </div>
      
      {selectedArticle && (
        <PDFViewer
          domainId={selectedArticle.domainId}
          articleNum={selectedArticle.articleNum}
          onClose={() => setSelectedArticle(null)}
        />
      )}
      
      <style jsx>{`
        .sources-list {
          margin-top: 1rem;
          padding: 1rem;
          background: #f8f9fa;
          border-radius: 8px;
        }
        
        .source-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem;
          margin: 0.5rem 0;
          background: white;
          border-radius: 4px;
        }
        
        .view-pdf-btn {
          background: #007bff;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
          transition: background 0.3s;
        }
        
        .view-pdf-btn:hover {
          background: #0056b3;
        }
        
        .hint {
          margin-top: 1rem;
          color: #666;
          font-size: 0.9rem;
        }
      `}</style>
    </>
  );
};