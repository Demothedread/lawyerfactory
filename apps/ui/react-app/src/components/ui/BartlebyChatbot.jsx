/**
 * BartlebyChatbot - AI Legal Clerk Assistant
 * 
 * An intelligent chatbot assistant that provides legal research support,
 * can modify case documents, and maintains context awareness of the entire
 * legal workflow. Named after the literary clerk Bartleby, but much more helpful.
 * 
 * Capabilities:
 * - Natural language queries about case evidence
 * - Modify skeletal outline structure
 * - Add/edit evidence table columns and entries
 * - Adjust research parameters for PhaseA02
 * - Semantic search across vector store
 * - Context-aware responses based on current workflow phase
 * - Soviet industrial themed UI
 */

import {
    AttachFile,
    Clear,
    Close,
    EditNote,
    ExpandLess,
    ExpandMore,
    Gavel,
    Menu,
    Send,
    Settings as SettingsIcon,
    TableChart,
} from '@mui/icons-material';
import {
    Button,
    Card,
    Chip,
    CircularProgress,
    Divider,
    Drawer,
    IconButton,
    InputAdornment,
    List,
    ListItemButton,
    ListItemText,
    Paper,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';
import { useCallback, useEffect, useRef, useState } from 'react';

import { backendService } from '../../services/backendService';
import { useToast } from '../feedback/Toast';

/**
 * Message type definitions
 */
const MessageType = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
  ACTION: 'action',
  ERROR: 'error',
};

/**
 * Action type definitions for document modifications
 */
const ActionType = {
  MODIFY_OUTLINE: 'modify_outline',
  UPDATE_EVIDENCE: 'update_evidence',
  ADJUST_RESEARCH: 'adjust_research',
  SEARCH_VECTORS: 'search_vectors',
  ADD_CLAIM: 'add_claim',
  EDIT_FACT: 'edit_fact',
};

const BartlebyChatbot = ({
  currentCaseId,
  settings,
  skeletalOutline,
  evidenceData,
  phaseStatuses,
  onOutlineUpdate,
  onEvidenceUpdate,
  onResearchUpdate,
}) => {
  // State management
  const [isOpen, setIsOpen] = useState(settings.bartlebyAutoOpen || false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [contextMenuOpen, setContextMenuOpen] = useState(false);
  const [costEstimate, setCostEstimate] = useState({ total: 0, session: 0 });
  const [attachedContext, setAttachedContext] = useState([]);

  const { addToast } = useToast();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: Date.now(),
          type: MessageType.SYSTEM,
          content:
            "⚖️ **Bartleby, Legal Clerk**\n\nI'm here to assist with your legal research and document preparation. I have access to your evidence store, case outline, and research data.\n\nYou can ask me to:\n- Search case evidence\n- Modify the skeletal outline\n- Add facts or claims\n- Adjust research parameters\n- Answer legal questions\n\nType `/help` for a list of commands.",
          timestamp: new Date(),
        },
      ]);
    }
  }, []);

  // Socket.IO integration for phase narration
  useEffect(() => {
    if (!currentCaseId) return;

    // Connect to backend Socket.IO
    const socket = io(import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000');

    // Join case session
    socket.emit('join_session', { case_id: currentCaseId });

    // Listen for phase narration from backend
    socket.on('bartleby_phase_narration', (data) => {
      const { phase, event, message, progress, details } = data;

      // Determine message styling based on event type
      let emoji = '📢';
      let messageType = MessageType.SYSTEM;

      if (event === 'started') {
        emoji = '🚀';
      } else if (event === 'completed') {
        emoji = '✅';
        messageType = MessageType.ACTION;
      } else if (event === 'error') {
        emoji = '❌';
        messageType = MessageType.ERROR;
      } else if (event === 'progress') {
        emoji = '⚙️';
      }

      // Add narration message to chat
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          type: messageType,
          content: `${emoji} **[${phase}]** ${message}`,
          timestamp: new Date(),
          metadata: { phase, event, progress, details },
        },
      ]);

      // Auto-open Bartleby if not already open during important events
      if ((event === 'started' || event === 'error') && !isOpen) {
        setIsOpen(true);
      }
    });

    // Listen for intervention responses
    socket.on('bartleby_intervention_response', (data) => {
      const { response, intervention_type } = data;

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          type: MessageType.ASSISTANT,
          content: response,
          timestamp: new Date(),
          metadata: { intervention_type },
        },
      ]);

      setIsTyping(false);
    });

    // Listen for errors
    socket.on('bartleby_error', (data) => {
      const { error, message: errorMessage } = data;

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          type: MessageType.ERROR,
          content: `❌ **Error**: ${errorMessage || error}`,
          timestamp: new Date(),
        },
      ]);

      setIsTyping(false);
      addToast('Bartleby encountered an error', 'error');
    });

    // Cleanup on unmount
    return () => {
      socket.emit('leave_session', { case_id: currentCaseId });
      socket.disconnect();
    };
  }, [currentCaseId, isOpen, addToast]);

  /**
   * Handle sending a message
   */
  const handleSendMessage = useCallback(async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: MessageType.USER,
      content: inputText,
      timestamp: new Date(),
      context: attachedContext,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    try {
      // Check for slash commands
      if (inputText.startsWith('/')) {
        await handleSlashCommand(inputText);
        return;
      }

      // Send to backend chat API
      const response = await backendService.sendChatMessage({
        message: inputText,
        caseId: currentCaseId,
        context: {
          outline: skeletalOutline,
          evidence: evidenceData,
          phases: phaseStatuses,
          attached: attachedContext,
        },
        settings: {
          model: settings.aiModel,
          provider: settings.llmProvider,
          temperature: settings.temperature,
          maxTokens: settings.maxTokens,
        },
      });

      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        type: MessageType.ASSISTANT,
        content: response.message,
        timestamp: new Date(),
        actions: response.actions || [],
        cost: response.cost,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Update cost estimate
      if (response.cost) {
        setCostEstimate((prev) => ({
          total: prev.total + response.cost,
          session: prev.session + response.cost,
        }));
      }

      // Handle any actions suggested by the assistant
      if (response.actions && response.actions.length > 0) {
        await handleActions(response.actions);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: MessageType.ERROR,
        content: `⚠️ Error: ${error.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);

      addToast(`${getIcon('error')} Chat error: ${error.message}`, {
        severity: 'error',
        title: 'Bartleby Error',
      });
    } finally {
      setIsTyping(false);
      setAttachedContext([]);
    }
  }, [inputText, currentCaseId, skeletalOutline, evidenceData, phaseStatuses, attachedContext, settings]);

  /**
   * Handle slash commands
   */
  const handleSlashCommand = async (command) => {
    setIsTyping(false);

    const cmd = command.toLowerCase().split(' ')[0];

    const commandResponses = {
      '/help': `**Available Commands:**\n\n\`/help\` - Show this help\n\`/clear\` - Clear chat history\n\`/context\` - Show attached context\n\`/outline\` - View skeletal outline\n\`/evidence\` - Show evidence summary\n\`/research\` - View research parameters\n\`/cost\` - Show usage costs\n\`/models\` - List available LLM models`,
      '/clear': null, // Special handling below
      '/context': `**Attached Context:**\n${attachedContext.length > 0 ? attachedContext.map((c) => `- ${c.type}: ${c.name}`).join('\n') : 'None'}`,
      '/outline': skeletalOutline
        ? `**Skeletal Outline:**\n\`\`\`\n${JSON.stringify(skeletalOutline, null, 2)}\n\`\`\``
        : 'No outline available yet.',
      '/evidence': evidenceData
        ? `**Evidence Summary:**\n${evidenceData.length || 0} evidence items loaded.`
        : 'No evidence loaded yet.',
      '/research': `**Research Parameters:**\nPhase: ${phaseStatuses.phaseA02 || 'Not started'}\nMode: ${settings.researchMode ? 'Enabled' : 'Disabled'}`,
      '/cost': `**💰 Usage Costs:**\n- Session: $${costEstimate.session.toFixed(4)}\n- Total: $${costEstimate.total.toFixed(4)}\n- Model: ${settings.aiModel}\n- Provider: ${settings.llmProvider}`,
      '/models': `**Available Models:**\n\n**OpenAI:**\n- gpt-5 (default)\n- gpt-5-mini\n- gpt-5-nano\n- gpt-4o\n- gpt-o1\n- gpt-o3\n\n**Anthropic:**\n- claude-3-5-sonnet-20241022\n- claude-3-opus-20240229\n- claude-3-haiku-20240307\n\n**Other:**\n- github-copilot\n- ollama-localhost\n\nChange in Settings ⚙️`,
    };

    if (cmd === '/clear') {
      setMessages([]);
      addToast(`${getIcon('complete')} Chat history cleared`, {
        severity: 'success',
        title: 'Cleared',
      });
      return;
    }

    const response = commandResponses[cmd] || `Unknown command: ${cmd}. Type \`/help\` for available commands.`;

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + 1,
        type: MessageType.SYSTEM,
        content: response,
        timestamp: new Date(),
      },
    ]);
  };

  /**
   * Handle actions suggested by the assistant
   */
  const handleActions = async (actions) => {
    for (const action of actions) {
      try {
        switch (action.type) {
          case ActionType.MODIFY_OUTLINE:
            if (onOutlineUpdate) {
              await onOutlineUpdate(action.data);
              addToast(`${getIcon('complete')} Skeletal outline updated`, {
                severity: 'success',
                title: 'Outline Modified',
              });
            }
            break;

          case ActionType.UPDATE_EVIDENCE:
            if (onEvidenceUpdate) {
              await onEvidenceUpdate(action.data);
              addToast(`${getIcon('complete')} Evidence table updated`, {
                severity: 'success',
                title: 'Evidence Modified',
              });
            }
            break;

          case ActionType.ADJUST_RESEARCH:
            if (onResearchUpdate) {
              await onResearchUpdate(action.data);
              addToast(`${getIcon('complete')} Research parameters adjusted`, {
                severity: 'success',
                title: 'Research Updated',
              });
            }
            break;

          case ActionType.SEARCH_VECTORS:
            // Vector search results displayed in message
            break;

          default:
            console.warn('Unknown action type:', action.type);
        }
      } catch (error) {
        console.error('Action execution error:', error);
        addToast(`${getIcon('error')} Failed to execute action: ${error.message}`, {
          severity: 'error',
          title: 'Action Failed',
        });
      }
    }
  };

  /**
   * Attach context to next message
   */
  const attachContext = (type, data) => {
    setAttachedContext((prev) => [...prev, { type, ...data }]);
    addToast(`${getIcon('complete')} Context attached: ${type}`, {
      severity: 'info',
      title: 'Context Added',
    });
  };

  /**
   * Render a single message
   */
  const renderMessage = (message) => {
    const isUser = message.type === MessageType.USER;
    const isSystem = message.type === MessageType.SYSTEM;
    const isError = message.type === MessageType.ERROR;
    const isAction = message.type === MessageType.ACTION;

    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
        }}
      >
        <Paper
          elevation={isUser ? 2 : 1}
          sx={{
            p: 1.5,
            maxWidth: '80%',
            bgcolor: isUser
              ? '#b87333' // Soviet brass
              : isSystem
              ? 'rgba(184, 115, 51, 0.1)' // Light brass
              : isError
              ? 'rgba(200, 50, 50, 0.2)' // Error red
              : isAction
              ? 'rgba(0, 200, 100, 0.2)' // Action green
              : 'background.paper',
            border: `1px solid ${isUser ? '#8b5a2b' : 'rgba(184, 115, 51, 0.3)'}`,
            borderRadius: isUser ? '12px 12px 0 12px' : '12px 12px 12px 0',
          }}
        >
          {/* Message header with timestamp */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography
              variant="caption"
              sx={{
                fontFamily: 'Courier New, monospace',
                color: isUser ? 'rgba(255,255,255,0.8)' : 'text.secondary',
                fontSize: '0.7rem',
              }}
            >
              {isUser ? 'You' : isSystem ? 'System' : isAction ? 'Action' : 'Bartleby'} •{' '}
              {message.timestamp.toLocaleTimeString()}
            </Typography>
            {message.cost && (
              <Chip
                label={`$${message.cost.toFixed(4)}`}
                size="small"
                sx={{
                  height: 16,
                  fontSize: '0.65rem',
                  fontFamily: 'Courier New, monospace',
                  bgcolor: 'rgba(0,0,0,0.2)',
                  color: isUser ? '#fff' : 'text.secondary',
                }}
              />
            )}
          </Box>

          {/* Message content */}
          <Typography
            variant="body2"
            sx={{
              color: isUser ? '#fff' : 'text.primary',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: message.content.includes('```') ? 'Courier New, monospace' : 'inherit',
            }}
          >
            {message.content}
          </Typography>

          {/* Attached context chips */}
          {message.context && message.context.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, mt: 1, flexWrap: 'wrap' }}>
              {message.context.map((ctx, idx) => (
                <Chip
                  key={idx}
                  label={ctx.type}
                  size="small"
                  icon={<AttachFile sx={{ width: 12, height: 12 }} />}
                  sx={{
                    height: 20,
                    fontSize: '0.7rem',
                    bgcolor: 'rgba(255,255,255,0.2)',
                    color: isUser ? '#fff' : 'text.secondary',
                  }}
                />
              ))}
            </Box>
          )}

          {/* Action buttons for assistant messages */}
          {message.actions && message.actions.length > 0 && (
            <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
              {message.actions.map((action, idx) => (
                <Button
                  key={idx}
                  size="small"
                  variant="outlined"
                  onClick={() => handleActions([action])}
                  sx={{
                    borderColor: '#b87333',
                    color: '#b87333',
                    fontSize: '0.7rem',
                    '&:hover': { borderColor: '#8b5a2b', bgcolor: 'rgba(184, 115, 51, 0.1)' },
                  }}
                >
                  {action.label || action.type}
                </Button>
              ))}
            </Box>
          )}
        </Paper>
      </Box>
    );
  };

  /**
   * Render typing indicator
   */
  const renderTypingIndicator = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Paper
        elevation={1}
        sx={{
          p: 1.5,
          bgcolor: 'background.paper',
          border: '1px solid rgba(184, 115, 51, 0.3)',
          borderRadius: '12px 12px 12px 0',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircularProgress size={16} sx={{ color: '#b87333' }} />
          <Typography variant="caption" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
            Bartleby is thinking...
          </Typography>
        </Box>
      </Paper>
    </Box>
  );

  /**
   * Context menu with quick actions
   */
  const renderContextMenu = () => (
    <Drawer anchor="right" open={contextMenuOpen} onClose={() => setContextMenuOpen(false)}>
      <Box sx={{ width: 280, p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2, fontFamily: 'Orbitron, monospace', color: '#b87333' }}>
          Quick Actions
        </Typography>

        <Divider sx={{ mb: 2 }} />

        <List>
          <ListItemButton onClick={() => attachContext('outline', { name: 'Skeletal Outline' })}>
            <EditNote sx={{ mr: 1 }} />
            <ListItemText primary="Attach Outline" secondary="Add outline context to next message" />
          </ListItemButton>

          <ListItemButton onClick={() => attachContext('evidence', { name: 'Evidence Table' })}>
            <TableChart sx={{ mr: 1 }} />
            <ListItemText primary="Attach Evidence" secondary="Add evidence table context" />
          </ListItemButton>

          <ListItemButton onClick={() => attachContext('phase', { name: 'Current Phase' })}>
            <Gavel sx={{ mr: 1 }} />
            <ListItemText primary="Attach Phase Status" secondary="Add current phase info" />
          </ListItemButton>

          <Divider sx={{ my: 2 }} />

          <ListItemButton onClick={() => handleSlashCommand('/cost')}>
            <SettingsIcon sx={{ mr: 1 }} />
            <ListItemText primary="View Costs" secondary={`Session: $${costEstimate.session.toFixed(4)}`} />
          </ListItemButton>
        </List>
      </Box>
    </Drawer>
  );

  // Main render
  if (!isOpen) {
    // Floating action button to open chat
    return (
      <>
        <Tooltip title="Open Bartleby Assistant" placement="left">
          <Button
            variant="contained"
            onClick={() => setIsOpen(true)}
            sx={{
              position: 'fixed',
              bottom: 20,
              right: 20,
              width: 60,
              height: 60,
              borderRadius: '50%',
              bgcolor: '#b87333',
              color: '#fff',
              fontFamily: 'Courier New, monospace',
              fontSize: '1.5rem',
              boxShadow: '0 4px 12px rgba(184, 115, 51, 0.5)',
              '&:hover': { bgcolor: '#8b5a2b', transform: 'scale(1.05)' },
              transition: 'all 0.3s ease',
              zIndex: 1300,
            }}
          >
            ⚖️
          </Button>
        </Tooltip>
      </>
    );
  }

  return (
    <>
      {/* Chatbot panel */}
      <Card
        sx={{
          position: 'fixed',
          bottom: isMinimized ? 0 : 20,
          right: 20,
          width: isMinimized ? 320 : 420,
          height: isMinimized ? 60 : 600,
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'background.paper',
          border: '2px solid #b87333',
          borderRadius: isMinimized ? '12px 12px 0 0' : '12px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
          transition: 'all 0.3s ease',
          zIndex: 1300,
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 1.5,
            bgcolor: '#b87333',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderRadius: isMinimized ? '10px 10px 0 0' : '10px 10px 0 0',
            cursor: 'pointer',
          }}
          onClick={() => setIsMinimized(!isMinimized)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" sx={{ fontFamily: 'Orbitron, monospace', fontSize: '1rem' }}>
              ⚖️ Bartleby
            </Typography>
            <Chip
              label="Legal Clerk"
              size="small"
              sx={{
                height: 20,
                fontSize: '0.65rem',
                bgcolor: 'rgba(255,255,255,0.2)',
                color: '#fff',
                fontFamily: 'Courier New, monospace',
              }}
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); setContextMenuOpen(true); }} sx={{ color: '#fff' }}>
              <Menu fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => setIsMinimized(!isMinimized)} sx={{ color: '#fff' }}>
              {isMinimized ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
            </IconButton>
            <IconButton size="small" onClick={() => setIsOpen(false)} sx={{ color: '#fff' }}>
              <Close fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {/* Messages area */}
        {!isMinimized && (
          <>
            <Box
              sx={{
                flex: 1,
                overflowY: 'auto',
                p: 2,
                bgcolor: 'rgba(0, 0, 0, 0.02)',
              }}
            >
              {messages.map(renderMessage)}
              {isTyping && renderTypingIndicator()}
              <div ref={messagesEndRef} />
            </Box>

            {/* Attached context display */}
            {attachedContext.length > 0 && (
              <Box sx={{ px: 2, py: 1, bgcolor: 'rgba(184, 115, 51, 0.1)', borderTop: '1px solid rgba(184, 115, 51, 0.3)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    Attached Context:
                  </Typography>
                  <IconButton size="small" onClick={() => setAttachedContext([])}>
                    <Clear fontSize="small" />
                  </IconButton>
                </Box>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {attachedContext.map((ctx, idx) => (
                    <Chip key={idx} label={ctx.type} size="small" sx={{ height: 20, fontSize: '0.7rem' }} />
                  ))}
                </Box>
              </Box>
            )}

            {/* Input area */}
            <Box sx={{ p: 2, borderTop: '2px solid rgba(184, 115, 51, 0.3)' }}>
              <TextField
                fullWidth
                multiline
                maxRows={3}
                placeholder="Ask Bartleby anything..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                inputRef={inputRef}
                disabled={isTyping}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={handleSendMessage}
                        disabled={!inputText.trim() || isTyping}
                        sx={{
                          color: '#b87333',
                          '&:hover': { bgcolor: 'rgba(184, 115, 51, 0.1)' },
                        }}
                      >
                        <Send />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '8px',
                    '&:hover fieldset': { borderColor: '#b87333' },
                    '&.Mui-focused fieldset': { borderColor: '#b87333' },
                  },
                }}
              />

              {/* Cost display */}
              {settings.showCostEstimates && (
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    mt: 0.5,
                    color: 'text.secondary',
                    fontFamily: 'Courier New, monospace',
                    fontSize: '0.7rem',
                  }}
                >
                  💰 Session: ${costEstimate.session.toFixed(4)} • Model: {settings.aiModel}
                </Typography>
              )}
            </Box>
          </>
        )}
      </Card>

      {/* Context menu drawer */}
      {renderContextMenu()}
    </>
  );
};

export default BartlebyChatbot;
