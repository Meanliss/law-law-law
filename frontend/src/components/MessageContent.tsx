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
  pdfSources?: Array<{ 
    json_file?: string; 
    pdf_file?: string; 
    article_num?: string; 
    page_num?: number;
    domain_id?: string;  // ✅ Add domain_id from backend
  }>;
  onOpenPDF?: (url: string, title: string, articleNum?: string, pageNum?: number) => void;
}

// Map json_file → domain_id (from domain_registry.json structure)
const jsonToDomainMap: Record<string, string> = {
  'luat_lao_dong_hopnhat.json': 'lao_dong',
  'luat_lao_donghopnhat.json': 'lao_dong',  // Alternative naming
  'luat_dauthau_hopnhat.json': 'dau_thau',
  'luat_dau_thau_hopnhat.json': 'dau_thau',  // Alternative naming
  'nghi_dinh_214_2025.json': 'dau_thau',
  'luat_dat_dai_hopnhat.json': 'dat_dai',
  'luat_hon_nhan_hopnhat.json': 'hon_nhan',
  'luat_hon_nhan.json': 'hon_nhan',  // Alternative naming
  'chuyen_giao_cong_nghe_hopnhat.json': 'chuyen_giao_cong_nghe',
  'luat_so_huu_tri_tue_hopnhat.json': 'lshtt',
  'luat_hinh_su_hopnhat.json': 'hinh_su',
};

// Map domain_id → display_name (pdf_file comes from backend)
const domainInfoMap: Record<string, { displayName: string }> = {
  'lao_dong': {
    displayName: 'Luật Lao động',
  },
  'dau_thau': {
    displayName: 'Luật Đấu thầu',
  },
  'dat_dai': {
    displayName: 'Luật Đất đai',
  },
  'hon_nhan': {
    displayName: 'Luật Hôn nhân và Gia đình',
  },
  'chuyen_giao_cong_nghe': {
    displayName: 'Luật Chuyển giao công nghệ',
  },
  'lshtt': {
    displayName: 'Bộ luật Sở hữu trí tuệ',
  },
  'hinh_su': {
    displayName: 'Bộ luật Hình sự',
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

  // ✅ Build map từ pdfSources: article_num → {domain_id, json_file, pdf_file}
  const articleToSourceMap: Record<string, { domain_id?: string; json_file: string; pdf_file: string }> = {};
  if (pdfSources && Array.isArray(pdfSources)) {
    pdfSources.forEach((source) => {
      if (source.article_num && source.pdf_file) {
        const articleKey = source.article_num;
        articleToSourceMap[articleKey] = {
          domain_id: source.domain_id,  // ✅ Use domain_id from backend
          json_file: source.json_file || '',
          pdf_file: source.pdf_file,
        };
        console.log('[MessageContent] Mapped article:', { 
          articleKey, 
          domainId: source.domain_id,
          jsonFile: source.json_file,
          pdfFile: source.pdf_file 
        });
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

    // ✅ Lấy source info từ map (domain_id + json_file + pdf_file)
    const sourceInfo = articleToSourceMap[articleNum] || {
      domain_id: undefined,
      json_file: 'luat_hon_nhan_hopnhat.json',
      pdf_file: 'luat_hon_nhan.pdf',
    };

    // Add hyperlink
    parts.push(
      <ArticleLink
        key={`article-${articleNum}-${khoans}-${idx}`}
        articleNum={articleNum}
        khoans={khoans}
        displayText={fullText}
        domainId={sourceInfo.domain_id}  // ✅ Pass domain_id directly
        jsonFile={sourceInfo.json_file}
        pdfFile={sourceInfo.pdf_file}
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
  domainId?: string;  // ✅ Use domain_id from backend
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
  // ✅ Use domain_id from backend, fallback to json_file mapping
  const resolvedDomainId = domainId || jsonToDomainMap[jsonFile] || 'hon_nhan';
  
  // ✅ Step 2: domain_id → displayName
  const displayName = domainInfoMap[resolvedDomainId]?.displayName || 'Văn bản pháp luật';

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onOpenPDF) {
      // ✅ Build correct PDF URL: backend/data/domains/{domain_id}/pdfs/{pdf_file}
      // Use actual pdf_file from backend instead of hardcoded mapping
      const pdfUrl = getPDFUrl(pdfFile);
      
      const articleRef = khoans ? `${articleNum} Khoản ${khoans}` : articleNum;
      console.log('[ArticleLink] Click:', { 
        articleNum, 
        jsonFile,
        pdfFile,
        domainId: resolvedDomainId,  // ✅ Log resolved domain_id
        pdfUrl, 
        pageNum,
        hasPageNum: pageNum !== undefined && pageNum > 0
      });
      
      // ✅ Pass pageNum to open correct page in PDF
      onOpenPDF(pdfUrl, displayName, articleNum, pageNum);
    }
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1 text-blue-600 dark:text-cyan-400 hover:underline hover:text-blue-700 dark:hover:text-cyan-300 font-medium transition-colors cursor-pointer bg-transparent border-none p-0"
      title={`Click để xem ${displayName} - Điều ${articleNum}`}
    >
      <span>{displayText}</span>
      <FileText size={12} className="inline opacity-60" />
    </button>
  );
}
