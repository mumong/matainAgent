"""
PDF 处理工具
用于从 PDF 文件中提取文本内容
"""
import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class PDFProcessor:
    """PDF 处理器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化 PDF 处理器
        
        Args:
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        从 PDF 文件中提取文本
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            提取的文本内容
        """
        if not HAS_PYMUPDF:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF processing. "
                "Install it with: pip install pymupdf"
            )
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        text_content = []
        doc = fitz.open(pdf_path)
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append(text)
        finally:
            doc.close()
        
        return "\n\n".join(text_content)
    
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """
        处理 PDF 文件，返回文档块列表
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            文档块列表
        """
        # 提取文本
        text = self.extract_text_from_pdf(pdf_path)
        
        # 分割文本
        chunks = self.text_splitter.split_text(text)
        
        # 创建 Document 对象
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": pdf_path,
                    "file_type": "pdf",
                    "chunk_index": i,
                    "filename": os.path.basename(pdf_path)
                }
            )
            documents.append(doc)
        
        return documents
