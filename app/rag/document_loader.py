"""
文档加载器
用于从 files 目录加载 txt 和 pdf 文件
"""
import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.pdf_utils import PDFProcessor


class DocumentLoader:
    """文档加载器"""
    
    def __init__(self, files_dir: str = None, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文档加载器
        
        Args:
            files_dir: 文件目录路径（默认为 app/rag/files）
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小
        """
        if files_dir is None:
            # 默认使用 app/rag/files 目录
            current_dir = Path(__file__).parent
            self.files_dir = current_dir / "files"
        else:
            self.files_dir = Path(files_dir)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        self.pdf_processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    def load_txt_file(self, file_path: Path) -> List[Document]:
        """
        加载 TXT 文件
        
        Args:
            file_path: TXT 文件路径
            
        Returns:
            文档块列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 分割文本
        chunks = self.text_splitter.split_text(text)
        
        # 创建 Document 对象
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": str(file_path),
                    "file_type": "txt",
                    "chunk_index": i,
                    "filename": file_path.name
                }
            )
            documents.append(doc)
        
        return documents
    
    def load_pdf_file(self, file_path: Path) -> List[Document]:
        """
        加载 PDF 文件
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            文档块列表
        """
        return self.pdf_processor.process_pdf(str(file_path))
    
    def load_all_documents(self) -> List[Document]:
        """
        加载 files 目录下的所有 txt 和 pdf 文件
        
        Returns:
            所有文档块列表
        """
        if not self.files_dir.exists():
            print(f"⚠️  文件目录不存在: {self.files_dir}")
            return []
        
        all_documents = []
        
        # 遍历文件目录
        for file_path in self.files_dir.iterdir():
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                
                try:
                    if file_ext == '.txt':
                        print(f"📄 加载 TXT 文件: {file_path.name}")
                        docs = self.load_txt_file(file_path)
                        all_documents.extend(docs)
                        print(f"   ✅ 加载了 {len(docs)} 个文档块")
                    
                    elif file_ext == '.pdf':
                        print(f"📕 加载 PDF 文件: {file_path.name}")
                        docs = self.load_pdf_file(file_path)
                        all_documents.extend(docs)
                        print(f"   ✅ 加载了 {len(docs)} 个文档块")
                    
                except Exception as e:
                    print(f"   ❌ 加载文件失败 {file_path.name}: {e}")
                    continue
        
        print(f"\n✅ 总共加载了 {len(all_documents)} 个文档块")
        return all_documents

