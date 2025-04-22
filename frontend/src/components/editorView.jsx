import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { pdfExporter } from 'quill-to-pdf';
import { saveAs } from 'file-saver';
import { generateWord } from 'quill-to-word';
import { useAuth } from '../contexts/AuthContext';
import AuthButton from './auth/AuthButton';
import axios from 'axios';
import '../styles/editorView.css';

const EditorView = () => {
  const [content, setContent] = useState('');
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadMessage, setDownloadMessage] = useState('');
  const [exportFormat, setExportFormat] = useState('docx');
  const [documentName, setDocumentName] = useState('ESRS Report');
  const [documentId, setDocumentId] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [documents, setDocuments] = useState([]);
  const [showDocumentsList, setShowDocumentsList] = useState(false);
  
  const quillRef = useRef(null);
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  useEffect(() => {
    // Load user documents if authenticated
    if (isAuthenticated) {
      fetchDocuments();
    }
  }, [isAuthenticated]);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get('/api/documents');
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const modules = {
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'list': 'ordered' }, { 'list': 'bullet' }],
      [{ 'indent': '-1' }, { 'indent': '+1' }],
      [{ 'align': [] }],
      [{ 'color': [] }, { 'background': [] }],
      ['clean']
    ]
  };

  const formats = [
    'header',
    'bold', 'italic', 'underline', 'strike',
    'list', 'bullet',
    'indent',
    'align',
    'color', 'background'
  ];

  const handleContentChange = (value) => {
    setContent(value);
  };

  const handleDocumentNameChange = (e) => {
    setDocumentName(e.target.value);
  };

  const handleFormatChange = (e) => {
    setExportFormat(e.target.value);
  };

  const saveDocument = async () => {
    if (!isAuthenticated) {
      setSaveMessage('You need to log in to save documents.');
      setTimeout(() => setSaveMessage(''), 3000);
      return;
    }

    if (!documentName.trim()) {
      setSaveMessage('Please enter a document name.');
      setTimeout(() => setSaveMessage(''), 3000);
      return;
    }

    setIsSaving(true);
    setSaveMessage('');

    try {
      let response;
      
      if (documentId) {
        // Update existing document
        response = await axios.put(`/api/documents/${documentId}`, {
          name: documentName,
          content: content
        });
        setSaveMessage('Document updated successfully!');
      } else {
        // Create new document
        response = await axios.post('/api/documents', {
          name: documentName,
          content: content
        });
        setDocumentId(response.data.document?.id);
        setSaveMessage('Document saved successfully!');
      }
      
      // Refresh documents list
      fetchDocuments();
    } catch (error) {
      console.error('Error saving document:', error);
      setSaveMessage('Error saving document. Please try again.');
    } finally {
      setIsSaving(false);
      setTimeout(() => setSaveMessage(''), 3000);
    }
  };

  const loadDocument = async (doc) => {
    try {
      const response = await axios.get(`/api/documents/${doc.id}`);
      if (response.data.document) {
        setContent(response.data.document.content);
        setDocumentName(response.data.document.name);
        setDocumentId(response.data.document.id);
      }
      setShowDocumentsList(false);
    } catch (error) {
      console.error('Error loading document:', error);
      setSaveMessage('Error loading document. Please try again.');
      setTimeout(() => setSaveMessage(''), 3000);
    }
  };

  const createNewDocument = () => {
    setContent('');
    setDocumentName('ESRS Report');
    setDocumentId(null);
    setShowDocumentsList(false);
  };

  const deleteDocument = async (id, e) => {
    e.stopPropagation();
    
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await axios.delete(`/api/documents/${id}`);
        fetchDocuments();
        
        if (documentId === id) {
          createNewDocument();
        }
      } catch (error) {
        console.error('Error deleting document:', error);
      }
    }
  };

  const handleExport = async () => {
    if (!content.trim()) {
      setDownloadMessage('Cannot download empty content.');
      setTimeout(() => setDownloadMessage(''), 3000);
      return;
    }
    
    setIsDownloading(true);
    setDownloadMessage('');
    
    try {
      if (exportFormat === 'pdf') {
        await exportToPDF();
      } else if (exportFormat === 'docx') {
        await exportToDOCX();
      } else if (exportFormat === 'txt') {
        exportToTXT();
      }
      
      setDownloadMessage(`${exportFormat.toUpperCase()} downloaded successfully.`);
      setTimeout(() => {
        setDownloadMessage('');
      }, 3000);
    } catch (error) {
      console.error(`Error downloading ${exportFormat.toUpperCase()}:`, error);
      setDownloadMessage(`Error downloading ${exportFormat.toUpperCase()}. Please try again.`);
    } finally {
      setIsDownloading(false);
    }
  };

  const exportToPDF = async () => {
    if (!quillRef.current) {
      setDownloadMessage('Editor not initialized. Please try again.');
      return;
    }
    
    const quillEditor = quillRef.current.getEditor();
    
    const pdfOptions = {
      filename: `${documentName}.pdf`,
      exportAs: 'blob',
      styleOptions: {
        paragraphSpacing: {
          before: 120,
          after: 240,
        },
        pageMargins: {
          top: 180,
          right: 180,
          bottom: 180,
          left: 180,
        },
      },
      title: documentName,
      author: 'ESGenerator',
      subject: 'European Sustainability Reporting Standards',
      keywords: 'ESRS, Sustainability, Report',
      headerText: documentName,
      footerText: `Generated on ${new Date().toLocaleDateString()}`,
    };
    
    const pdfBlob = await pdfExporter.generatePdf(quillEditor.getContents(), pdfOptions);
    
    if (window.showSaveFilePicker) {
      try {
        const opts = {
          suggestedName: `${documentName}.pdf`,
          types: [{
            description: 'PDF File',
            accept: {'application/pdf': ['.pdf']}
          }]
        };
        
        const fileHandle = await window.showSaveFilePicker(opts);
        const writable = await fileHandle.createWritable();
        await writable.write(pdfBlob);
        await writable.close();
      } catch (err) {
        if (err.name !== 'AbortError') {
          saveAs(pdfBlob, `${documentName}.pdf`);
        }
      }
    } else {
      saveAs(pdfBlob, `${documentName}.pdf`);
    }
  };

  const exportToDOCX = async () => {
    if (!quillRef.current) {
      setDownloadMessage('Editor not initialized. Please try again.');
      return;
    }
    
    const quillEditor = quillRef.current.getEditor();
    
    const docxOptions = {
      exportAs: 'blob',
      styleOptions: {
        paragraphSpacing: {
          before: 120,
          after: 240,
        },
        pageMargins: {
          top: 360, 
          right: 360,
          bottom: 360,
          left: 360,
        },
      },
      title: documentName,
      subject: 'European Sustainability Reporting Standards',
      creator: 'ESGenerator',
      description: 'ESRS Report generated with ESGenerator',
      lastModifiedBy: 'ESGenerator User',
    };
    
    const docxBlob = await generateWord(quillEditor.getContents(), docxOptions);
    
    if (window.showSaveFilePicker) {
      try {
        const opts = {
          suggestedName: `${documentName}.docx`,
          types: [{
            description: 'Word Document',
            accept: {'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']}
          }]
        };
        
        const fileHandle = await window.showSaveFilePicker(opts);
        const writable = await fileHandle.createWritable();
        await writable.write(docxBlob);
        await writable.close();
      } catch (err) {
        if (err.name !== 'AbortError') {
          saveAs(docxBlob, `${documentName}.docx`);
        }
      }
    } else {
      saveAs(docxBlob, `${documentName}.docx`);
    }
  };

  const exportToTXT = () => {
    if (!quillRef.current) {
      setDownloadMessage('Editor not initialized. Please try again.');
      return;
    }
    
    const quillEditor = quillRef.current.getEditor();
    const plainText = quillEditor.getText();
    const txtBlob = new Blob([plainText], { type: 'text/plain;charset=utf-8' });
    
    if (window.showSaveFilePicker) {
      try {
        const opts = {
          suggestedName: `${documentName}.txt`,
          types: [{
            description: 'Text File',
            accept: {'text/plain': ['.txt']}
          }]
        };
        
        window.showSaveFilePicker(opts)
          .then(fileHandle => fileHandle.createWritable())
          .then(writable => {
            writable.write(txtBlob);
            return writable.close();
          })
          .catch(err => {
            if (err.name !== 'AbortError') {
              saveAs(txtBlob, `${documentName}.txt`);
            }
          });
      } catch (err) {
        saveAs(txtBlob, `${documentName}.txt`);
      }
    } else {
      saveAs(txtBlob, `${documentName}.txt`);
    }
  };

  return (
    <div className="container">
      <div className="top-bar">
        <div className="nav-container">
          <button 
            className="nav-button inactive" 
            onClick={() => navigate('/')}
          >
            Chat
          </button>
          <button className="nav-button active">Editor</button>
        </div>
        <AuthButton />
      </div>
      
      <div className="header">
        <h1>ESGenerator - Editor</h1>
      </div>
      
      <div className="editor-container">
        <div className="editor-toolbar">
          <div className="document-controls">
            <input
              type="text"
              className="document-name-input"
              value={documentName}
              onChange={handleDocumentNameChange}
              placeholder="Document name"
            />
            
            <button 
              className="save-button"
              onClick={saveDocument}
              disabled={isSaving || !isAuthenticated}
              title={isAuthenticated ? "Save document" : "Log in to save documents"}
            >
              {isSaving ? "Saving..." : "Save"}
            </button>
            
            {isAuthenticated && (
              <div className="documents-dropdown">
                <button 
                  className="documents-button"
                  onClick={() => setShowDocumentsList(!showDocumentsList)}
                >
                  Documents
                </button>
                
                {showDocumentsList && (
                  <div className="documents-list">
                    <button 
                      className="new-document-button"
                      onClick={createNewDocument}
                    >
                      + New Document
                    </button>
                    
                    {documents.length > 0 ? (
                      documents.map(doc => (
                        <div 
                          key={doc.id} 
                          className="document-item"
                          onClick={() => loadDocument(doc)}
                        >
                          <span>{doc.name}</span>
                          <button 
                            className="delete-document-button"
                            onClick={(e) => deleteDocument(doc.id, e)}
                          >
                            ×
                          </button>
                        </div>
                      ))
                    ) : (
                      <div className="no-documents">No saved documents</div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
          
          {saveMessage && (
            <div className={`save-message ${saveMessage.includes('Error') || saveMessage.includes('need to log in') ? 'error' : 'success'}`}>
              {saveMessage}
            </div>
          )}
        </div>
        
        <div className="quill-wrapper">
          <ReactQuill
            ref={quillRef}
            theme="snow"
            value={content}
            onChange={handleContentChange}
            modules={modules}
            formats={formats}
            placeholder="Write your ESRS report here..."
          />
        </div>
        
        <div className="editor-controls">
          {downloadMessage && (
            <div className={`save-message ${downloadMessage.includes('Error') || downloadMessage.includes('Cannot') ? 'error' : 'success'}`}>
              {downloadMessage}
            </div>
          )}
          
          <div className="export-options">
            <select 
              className="format-selector" 
              value={exportFormat} 
              onChange={handleFormatChange}
            >
              <option value="pdf">PDF</option>
              <option value="docx">Word Document (.docx)</option>
              <option value="txt">Plain Text (.txt)</option>
            </select>
            
            <button 
              className="export-button"
              onClick={handleExport}
              disabled={isDownloading}
            >
              {isDownloading ? `Preparing ${exportFormat.toUpperCase()}...` : `Download ${exportFormat.toUpperCase()}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditorView;