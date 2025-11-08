import { FileText } from 'lucide-react';
import { getPDFUrl } from '../services/api';

/**
 * Component để render AI message text với hyperlinks cho các Điều luật
 * 
 * Regex pattern: "Điều XXX Khoản Y" hoặc "[X] filename.json"
 * → Chuyển thành hyperlink có thể click
 */

interface MessageContentProps {
  text: string;
  pdfSources?: Array<{ json_file?: string; pdf_file?: string; article_num?: string; page_num?: number }>;
  onOpenPDF?: (url: string, title: string, articleNum?: string, pageNum?: number) => void;
}

// Map filename → {displayName}
// PDF filename được generate từ json filename
const lawFileMap: Record<string, { pdfName: string; displayName: string }> = {
  'luat_hon_nhan_hopnhat.json': {
    pdfName: 'luat_hon_nhan.pdf',
    displayName: 'Luật Hôn nhân và Gia đình',
  },
  'luat_hinh_su_hopnhat.json': {
    pdfName: 'luat_hinh_su.pdf',
    displayName: 'Bộ luật Hình sự',
  },
  'luat_lao_donghopnhat.json': {
    pdfName: 'luat_lao_dong.pdf',
    displayName: 'Bộ luật Lao động',
  },
  'luat_dat_dai_hopnhat.json': {
    pdfName: 'luat_dat_dai.pdf',
    displayName: 'Luật Đất đai',
  },
  'luat_dauthau_hopnhat.json': {
    pdfName: 'luat_dau_thau.pdf',
    displayName: 'Luật Đấu thầu',
  },
  'chuyen_giao_cong_nghe_hopnhat.json': {
    pdfName: 'luat_chuyen_giao_cong_nghe.pdf',
    displayName: 'Luật Chuyển giao công nghệ',
  },
  'luat_so_huu_tri_tue_hopnhat.json': {
    pdfName: 'luat_so_huu_tri_tue.pdf',
    displayName: 'Bộ luật Sở hữu trí tuệ',
  },
};

export function MessageContent({ text, pdfSources, onOpenPDF }: MessageContentProps) {
  // ✅ NUKE ALL .json references from text - ANY format the backend sends
  // We don't want ANY .json file names showing in the message
  let cleanText = text
    .replace(/\[[\d,\s]*\]\s*[\w_\-\.]*\.json\b/gi, '')  // [1] file.json, [1,2] file.json
    .replace(/\[\s*[\w_\-\.]+\.json\s*\]/gi, '')         // [file.json]
    .replace(/\bcủa\s+[\w_\-\.]+\.json\b/gi, '')         // của file.json
    .replace(/[\w_\-\.]+\.json\b(?=[\s,.);\n]|$)/gi, '') // file.json standalone
    .replace(/\s+/g, ' ')  // Clean multiple spaces
    .trim();
  
  console.log('[MessageContent] BEFORE cleanup:', text.substring(0, 100));
  console.log('[MessageContent] AFTER cleanup:', cleanText.substring(0, 100));

  // Regex để match: "Điều XXX Khoản Y"
  const articleRegex = /Điều\s+(\d+)(?:\s+Khoản\s+(\d+))?/g;

  // Parse text và tạo hyperlinks
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // ✅ Build map từ pdfSources: article_num → json_file
  const articleToJsonMap: Record<string, string> = {};
  if (pdfSources && Array.isArray(pdfSources)) {
    pdfSources.forEach((source) => {
      if (source.article_num && source.json_file) {
        // Map article "Điều XXX" to JSON filename
        const articleKey = source.article_num;
        articleToJsonMap[articleKey] = source.json_file;
        console.log('[MessageContent] Mapped article:', { articleKey, jsonFile: source.json_file });
      }
    });
  }

  // Split text bằng article references
  const articleMatches = [...cleanText.matchAll(articleRegex)];

  if (articleMatches.length === 0) {
    // Không có article references → return clean text
    return <div className="whitespace-pre-wrap break-words">{cleanText}</div>;
  }

  // Build parts với hyperlinks
  articleMatches.forEach((match, idx) => {
    const articleNum = match[1];
    const khoans = match[2] || '';
    const fullText = match[0]; // "Điều XXX" hoặc "Điều XXX Khoản Y"

    // Add text trước link
    if (match.index !== undefined && match.index > lastIndex) {
      parts.push(cleanText.substring(lastIndex, match.index));
    }

    // ✅ Lấy JSON filename từ map
    const jsonFile = articleToJsonMap[articleNum] || 'luat_hon_nhan_hopnhat.json';

    // Add hyperlink
    parts.push(
      <ArticleLink
        key={`article-${articleNum}-${khoans}-${idx}`}
        articleNum={articleNum}
        khoans={khoans}
        displayText={fullText}
        lawFile={jsonFile}
        pageNum={pdfSources?.find(s => s.article_num === articleNum)?.page_num}
        onOpenPDF={onOpenPDF}
      />
    );

    lastIndex = (match.index || 0) + fullText.length;
  });

  // Add remaining text
  if (lastIndex < cleanText.length) {
    const remaining = cleanText.substring(lastIndex).trim();
    if (remaining) {
      parts.push(remaining);
    }
  }

  return <div className="whitespace-pre-wrap break-words">{parts}</div>;
}

interface ArticleLinkProps {
  articleNum: string;
  khoans: string;
  displayText: string;
  lawFile: string;
  pageNum?: number;
  onOpenPDF?: (url: string, title: string, articleNum?: string, pageNum?: number) => void;
}

function ArticleLink({
  articleNum,
  khoans,
  displayText,
  lawFile,
  pageNum,
  onOpenPDF,
}: ArticleLinkProps) {
  const lawInfo = lawFileMap[lawFile] || {
    pdfName: 'luat_hon_nhan.pdf',
    displayName: 'Văn bản pháp luật',
  };

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onOpenPDF) {
      // Use getPDFUrl to build correct URL with API_BASE detection
      const pdfUrl = getPDFUrl(lawInfo.pdfName);
      
      const articleRef = khoans ? `${articleNum} Khoản ${khoans}` : articleNum;
      console.log('[ArticleLink] Opening:', { pdfUrl, lawInfo, articleRef, pageNum });
      
      onOpenPDF(pdfUrl, lawInfo.displayName, articleNum, pageNum);
    }
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1 text-blue-600 dark:text-cyan-400 hover:underline hover:text-blue-700 dark:hover:text-cyan-300 font-medium transition-colors cursor-pointer bg-transparent border-none p-0"
      title={`Click để xem ${lawInfo.displayName} - Điều ${articleNum}`}
    >
      <span>{displayText}</span>
      <FileText size={12} className="inline opacity-60" />
    </button>
  );
}
