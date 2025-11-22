import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileText } from 'lucide-react';
import { getPDFUrl } from '../services/api';

/**
 * Component để render AI message text với Markdown và hyperlinks cho các Điều luật
 */

interface MessageContentProps {
  text: string;
  pdfSources?: Array<{
    json_file?: string;
    pdf_file?: string;
    article_num?: string;
    page_num?: number;
    domain_id?: string;
  }>;
  onOpenPDF?: (url: string, title: string, articleNum?: string, pageNum?: number) => void;
}

// Map json_file → domain_id (from domain_registry.json structure)
const jsonToDomainMap: Record<string, string> = {
  'luat_lao_dong_hopnhat.json': 'lao_dong',
  'luat_lao_donghopnhat.json': 'lao_dong',
  'luat_dauthau_hopnhat.json': 'dau_thau',
  'luat_dau_thau_hopnhat.json': 'dau_thau',
  'nghi_dinh_214_2025.json': 'dau_thau',
  'luat_dat_dai_hopnhat.json': 'dat_dai',
  'luat_hon_nhan_hopnhat.json': 'hon_nhan',
  'luat_hon_nhan.json': 'hon_nhan',
  'chuyen_giao_cong_nghe_hopnhat.json': 'chuyen_giao_cong_nghe',
  'luat_so_huu_tri_tue_hopnhat.json': 'lshtt',
  'luat_hinh_su_hopnhat.json': 'hinh_su',
};

// Map domain_id → display_name
const domainInfoMap: Record<string, { displayName: string }> = {
  'lao_dong': { displayName: 'Luật Lao động' },
  'dau_thau': { displayName: 'Luật Đấu thầu' },
  'dat_dai': { displayName: 'Luật Đất đai' },
  'hon_nhan': { displayName: 'Luật Hôn nhân và Gia đình' },
  'chuyen_giao_cong_nghe': { displayName: 'Luật Chuyển giao công nghệ' },
  'lshtt': { displayName: 'Bộ luật Sở hữu trí tuệ' },
  'hinh_su': { displayName: 'Bộ luật Hình sự' },
};

export function MessageContent({ text, pdfSources, onOpenPDF }: MessageContentProps) {
  // 1. CLEANUP: Remove .json references
  let cleanText = text
    .replace(/\[[\d,\s]*\]\s*[\w_\-\.]*\.json\b/gi, '')
    .replace(/\[\s*[\w_\-\.]+\.json\s*\]/gi, '')
    .replace(/\bcủa\s+[\w_\-\.]+\.json\b/gi, '')
    .replace(/[\w_\-\.]+\.json\b(?=[\s,.);\n]|$)/gi, '')
    .trim();

  // 2. PRE-PROCESS: Convert "Điều X" to Markdown links [Điều X](article:X)
  // Regex to match "Điều XXX" or "Điều XXX Khoản Y"
  // We use a special protocol "article:" to identify these links later
  const articleRegex = /(Điều\s+(\d+)(?:\s+Khoản\s+(\d+))?)/g;

  const markdownText = cleanText.replace(articleRegex, (match, fullText, articleNum, khoans) => {
    // Create a unique key for the link: article:123:1 (Article 123, Clause 1)
    // If clause is missing, it's just article:123
    const linkKey = khoans ? `article:${articleNum}:${khoans}` : `article:${articleNum}`;
    return `[${fullText}](${linkKey})`;
  });

  // 3. PREPARE SOURCE MAP
  const articleToSourceMap: Record<string, { domain_id?: string; json_file: string; pdf_file: string; page_num?: number }> = {};
  if (pdfSources && Array.isArray(pdfSources)) {
    pdfSources.forEach((source) => {
      if (source.article_num && source.pdf_file) {
        articleToSourceMap[source.article_num] = {
          domain_id: source.domain_id,
          json_file: source.json_file || '',
          pdf_file: source.pdf_file,
          page_num: source.page_num
        };
      }
    });
  }

  // 4. CUSTOM RENDERER for links
  const components = {
    a: ({ href, children, ...props }: any) => {
      if (href && href.startsWith('article:')) {
        const parts = href.split(':');
        const articleNum = parts[1];
        const khoans = parts[2] || '';

        // Get source info
        const sourceInfo = articleToSourceMap[articleNum] || {
          domain_id: undefined,
          json_file: 'luat_hon_nhan_hopnhat.json',
          pdf_file: 'luat_hon_nhan.pdf',
        };

        return (
          <ArticleLink
            articleNum={articleNum}
            khoans={khoans}
            displayText={String(children)}
            domainId={sourceInfo.domain_id}
            jsonFile={sourceInfo.json_file}
            pdfFile={sourceInfo.pdf_file}
            pageNum={sourceInfo.page_num}
            onOpenPDF={onOpenPDF}
          />
        );
      }
      // Normal link
      return <a href={href} {...props} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>;
    },
    // Custom styling for other elements
    p: ({ children }: any) => <p className="mb-4 leading-relaxed last:mb-0">{children}</p>,
    ul: ({ children }: any) => <ul className="list-disc pl-5 mb-4 space-y-1">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal pl-5 mb-4 space-y-1">{children}</ol>,
    li: ({ children }: any) => <li className="leading-relaxed">{children}</li>,
    strong: ({ children }: any) => <strong className="font-bold text-gray-900 dark:text-gray-100">{children}</strong>,
    h1: ({ children }: any) => <h1 className="text-xl font-bold mb-2 mt-4">{children}</h1>,
    h2: ({ children }: any) => <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>,
    h3: ({ children }: any) => <h3 className="text-md font-bold mb-1 mt-2">{children}</h3>,
    blockquote: ({ children }: any) => <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4 text-gray-600 dark:text-gray-400">{children}</blockquote>,
  };

  return (
    <div className="markdown-content text-sm md:text-base text-gray-800 dark:text-gray-200">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
        urlTransform={(uri) => {
          // ✅ Preserve custom article: protocol, don't sanitize it
          if (uri.startsWith('article:')) {
            return uri;
          }
          // For other URIs, use default behavior
          return uri;
        }}
      >
        {markdownText}
      </ReactMarkdown>
    </div>
  );
}

interface ArticleLinkProps {
  articleNum: string;
  khoans: string;
  displayText: string;
  domainId?: string;
  jsonFile: string;
  pdfFile: string;
  pageNum?: number;
  onOpenPDF?: (url: string, title: string, articleNum?: string, pageNum?: number) => void;
}

function ArticleLink({
  articleNum,
  khoans,
  displayText,
  domainId,
  jsonFile,
  pdfFile,
  pageNum,
  onOpenPDF,
}: ArticleLinkProps) {
  const resolvedDomainId = domainId || jsonToDomainMap[jsonFile] || 'hon_nhan';
  const displayName = domainInfoMap[resolvedDomainId]?.displayName || 'Văn bản pháp luật';

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onOpenPDF) {
      const pdfUrl = getPDFUrl(pdfFile);
      onOpenPDF(pdfUrl, displayName, articleNum, pageNum);
    }
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1 text-blue-600 dark:text-cyan-400 hover:underline hover:text-blue-700 dark:hover:text-cyan-300 font-medium transition-colors cursor-pointer bg-transparent border-none p-0 mx-1"
      title={`Click để xem ${displayName} - Điều ${articleNum}`}
    >
      <span>{displayText}</span>
      <FileText size={12} className="inline opacity-60" />
    </button>
  );
}
