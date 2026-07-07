import { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import TopNav from './components/TopNav';
import JdLanding from './components/jd/JdLanding';
import JdLobDashboard from './components/jd/JdLobDashboard';
import JdWizard from './components/jd/JdWizard';
import JdGeneratedPanel from './components/jd/JdGeneratedPanel';
import { api } from './api';
import { jdApi } from './jdApi';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const [jdConfig, setJdConfig] = useState(null);
  const [jdDrafts, setJdDrafts] = useState([]);
  const [selectedLob, setSelectedLob] = useState(null);
  const [currentJdDraft, setCurrentJdDraft] = useState(null);
  const [jdDetailTab, setJdDetailTab] = useState('editor');

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
    loadJdConfig();
    loadJdDrafts();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const loadJdConfig = async () => {
    try {
      const cfg = await jdApi.getConfig();
      setJdConfig(cfg);
    } catch (error) {
      console.error('Failed to load JD config:', error);
    }
  };

  const loadJdDrafts = async () => {
    try {
      const drafts = await jdApi.listDrafts();
      setJdDrafts(drafts);
    } catch (error) {
      console.error('Failed to load JD drafts:', error);
    }
  };

  const handleSelectLob = (lob) => {
    setSelectedLob(lob);
    setCurrentJdDraft(null);
  };

  const handleBackToLobPicker = () => {
    setSelectedLob(null);
  };

  const handleBackToDashboard = () => {
    setCurrentJdDraft(null);
  };

  const handleCreateJdForLob = async (lob) => {
    try {
      const draft = await jdApi.createDraft(lob);
      setSelectedLob(lob);
      setCurrentJdDraft(draft);
      setJdDetailTab('editor');
      loadJdDrafts();
    } catch (error) {
      console.error('Failed to create JD draft:', error);
    }
  };

  const handleDownloadJdTemplate = async (lob) => {
    try {
      await jdApi.downloadTemplate(lob);
    } catch (error) {
      console.error('Failed to download JD template:', error);
    }
  };

  const handleDownloadJdSampleTemplate = async (lob) => {
    try {
      await jdApi.downloadSampleTemplate(lob);
    } catch (error) {
      console.error('Failed to download JD sample template:', error);
    }
  };

  const handleUploadJdForLob = async (lob, file) => {
    const { draft, warnings } = await jdApi.uploadDraft(lob, file);
    setSelectedLob(lob);
    setCurrentJdDraft(draft);
    setJdDetailTab('editor');
    loadJdDrafts();
    return warnings;
  };

  const handleSelectJdDraft = async (id) => {
    try {
      const draft = await jdApi.getDraft(id);
      setSelectedLob(draft.lob);
      setCurrentJdDraft(draft);
      setJdDetailTab('editor');
    } catch (error) {
      console.error('Failed to load JD draft:', error);
    }
  };

  const handleJdDraftUpdated = (updatedDraft) => {
    setCurrentJdDraft(updatedDraft);
    loadJdDrafts();
  };

  const handleDeleteJdDraft = async (id) => {
    try {
      await jdApi.deleteDraft(id);
      loadJdDrafts();
      if (currentJdDraft?.id === id) {
        setCurrentJdDraft(null);
      }
    } catch (error) {
      console.error('Failed to delete JD draft:', error);
    }
  };

  const handleSelectJdDetailTab = async (tab) => {
    setJdDetailTab(tab);
    if (tab === 'chat' && currentJdDraft) {
      try {
        let conversationId = currentJdDraft.linked_conversation_id;
        if (!conversationId) {
          const result = await jdApi.linkConversation(currentJdDraft.id);
          conversationId = result.conversation_id;
          setCurrentJdDraft((prev) => ({ ...prev, linked_conversation_id: conversationId }));
          loadJdDrafts();
        }
        setCurrentConversationId(conversationId);
      } catch (error) {
        console.error('Failed to link conversation:', error);
      }
    }
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = event.data;
              lastMsg.metadata = event.metadata;
              lastMsg.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = event.data;
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <TopNav />
      <div className="app">
        {!selectedLob ? (
          <JdLanding config={jdConfig} onSelectLob={handleSelectLob} />
        ) : !currentJdDraft ? (
          <JdLobDashboard
            lob={selectedLob}
            config={jdConfig}
            drafts={jdDrafts}
            onSelectDraft={handleSelectJdDraft}
            onNewDraft={handleCreateJdForLob}
            onDownloadTemplate={handleDownloadJdTemplate}
            onDownloadSampleTemplate={handleDownloadJdSampleTemplate}
            onUploadDraft={handleUploadJdForLob}
            onBack={handleBackToLobPicker}
            onDeleteDraft={handleDeleteJdDraft}
          />
        ) : currentJdDraft.status === 'draft' ? (
          <JdWizard
            draft={currentJdDraft}
            config={jdConfig}
            onDraftUpdated={handleJdDraftUpdated}
            onBackToDashboard={handleBackToDashboard}
            onDeleteDraft={handleDeleteJdDraft}
          />
        ) : (
          <JdGeneratedPanel
            draft={currentJdDraft}
            activeTab={jdDetailTab}
            onSelectTab={handleSelectJdDetailTab}
            onBackToDashboard={handleBackToDashboard}
          >
            {jdDetailTab === 'editor' ? (
              <JdWizard
                draft={currentJdDraft}
                config={jdConfig}
                onDraftUpdated={handleJdDraftUpdated}
              />
            ) : (
              <ChatInterface
                conversation={currentConversation}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
              />
            )}
          </JdGeneratedPanel>
        )}
      </div>
    </div>
  );
}

export default App;
