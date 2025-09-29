// AgentOrchestrationPanel - Real-time visualization of 7-agent collaboration system
import {
  AccountTree,
  Assessment,
  Business,
  Edit,
  FileCopy,
  Gavel,
  Memory,
  Refresh,
  Router,
  Search,
  Speed,
} from "@mui/icons-material";
import {
  Avatar,
  Badge,
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";

// Soviet-style components
import { MechanicalButton, NixieDisplay } from "../soviet";

const AgentOrchestrationPanel = ({
  socket,
  collapsed = false,
  onToggleCollapsed,
}) => {
  const [agentStates, setAgentStates] = useState({});
  const [swarmActivity, setSwarmActivity] = useState([]);
  const [communicationLog, setCommunicationLog] = useState([]);
  const [networkMetrics, setNetworkMetrics] = useState({
    totalMessages: 0,
    activeConnections: 0,
    avgResponseTime: 0,
    errorRate: 0,
  });

  const svgRef = useRef(null);

  // Agent definitions with enhanced metadata
  const agentDefinitions = {
    maestro: {
      name: "Maestro",
      role: "Central Coordinator",
      icon: <AccountTree sx={{ color: "#FFD700" }} />,
      color: "#FFD700", // Gold
      position: { x: 50, y: 20 }, // Center top
      description: "Orchestrates workflow, manages agent communication",
    },
    reader: {
      name: "Reader",
      role: "Document Intake",
      icon: <FileCopy sx={{ color: "#4CAF50" }} />,
      color: "#4CAF50", // Green
      position: { x: 20, y: 50 }, // Left
      description: "Processes documents, extracts entities",
    },
    researcher: {
      name: "Researcher",
      role: "Legal Research",
      icon: <Search sx={{ color: "#2196F3" }} />,
      color: "#2196F3", // Blue
      position: { x: 35, y: 35 }, // Top left
      description: "Conducts case law research, finds precedents",
    },
    outliner: {
      name: "Outliner",
      role: "Case Structure",
      icon: <Assessment sx={{ color: "#FF9800" }} />,
      color: "#FF9800", // Orange
      position: { x: 65, y: 35 }, // Top right
      description: "Creates outlines, identifies legal elements",
    },
    writer: {
      name: "Writer",
      role: "Document Drafting",
      icon: <Edit sx={{ color: "#9C27B0" }} />,
      color: "#9C27B0", // Purple
      position: { x: 80, y: 50 }, // Right
      description: "Generates legal documents, applies templates",
    },
    editor: {
      name: "Editor",
      role: "Quality Assurance",
      icon: <Gavel sx={{ color: "#F44336" }} />,
      color: "#F44336", // Red
      position: { x: 65, y: 65 }, // Bottom right
      description: "Reviews content, validates accuracy",
    },
    paralegal: {
      name: "Paralegal",
      role: "Evidence Management",
      icon: <Business sx={{ color: "#607D8B" }} />,
      color: "#607D8B", // Blue Grey
      position: { x: 35, y: 65 }, // Bottom left
      description: "Manages evidence, validates procedures",
    },
  };

  // Initialize agent states
  useEffect(() => {
    const initialStates = {};
    Object.keys(agentDefinitions).forEach((agentId) => {
      initialStates[agentId] = {
        status: "idle", // idle, active, busy, error, completed
        task: null,
        progress: 0,
        cpuUsage: Math.random() * 20 + 5, // 5-25%
        memoryUsage: Math.random() * 30 + 10, // 10-40%
        lastActivity: Date.now(),
        messagesProcessed: 0,
        currentPhase: null,
        estimatedCompletion: null,
      };
    });
    setAgentStates(initialStates);
  }, []);

  // Socket.IO event handlers for real-time updates
  useEffect(() => {
    if (!socket) return;

    const handleAgentUpdate = (data) => {
      const { agentId, status, task, progress, phase } = data;
      setAgentStates((prev) => ({
        ...prev,
        [agentId]: {
          ...prev[agentId],
          status,
          task,
          progress: progress || prev[agentId].progress,
          currentPhase: phase,
          lastActivity: Date.now(),
          messagesProcessed: prev[agentId].messagesProcessed + 1,
        },
      }));
    };

    const handleSwarmActivity = (data) => {
      setSwarmActivity((prev) => [
        { ...data, timestamp: Date.now(), id: Date.now() + Math.random() },
        ...prev.slice(0, 49), // Keep last 50 activities
      ]);
    };

    const handleAgentCommunication = (data) => {
      setCommunicationLog((prev) => [
        { ...data, timestamp: Date.now(), id: Date.now() + Math.random() },
        ...prev.slice(0, 99), // Keep last 100 messages
      ]);

      // Update network metrics
      setNetworkMetrics((prev) => ({
        ...prev,
        totalMessages: prev.totalMessages + 1,
        avgResponseTime: data.responseTime || prev.avgResponseTime,
      }));
    };

    socket.on("agent_status", handleAgentUpdate);
    socket.on("swarm_activity", handleSwarmActivity);
    socket.on("agent_communication", handleAgentCommunication);

    return () => {
      socket.off("agent_status", handleAgentUpdate);
      socket.off("swarm_activity", handleSwarmActivity);
      socket.off("agent_communication", handleAgentCommunication);
    };
  }, [socket]);

  // Simulate real-time updates for demonstration
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate agent activity updates
      const agentIds = Object.keys(agentDefinitions);
      const randomAgent = agentIds[Math.floor(Math.random() * agentIds.length)];

      setAgentStates((prev) => ({
        ...prev,
        [randomAgent]: {
          ...prev[randomAgent],
          cpuUsage: Math.max(
            5,
            Math.min(
              95,
              prev[randomAgent].cpuUsage + (Math.random() - 0.5) * 10
            )
          ),
          memoryUsage: Math.max(
            5,
            Math.min(
              95,
              prev[randomAgent].memoryUsage + (Math.random() - 0.5) * 8
            )
          ),
          lastActivity: Date.now(),
        },
      }));

      // Simulate communication activity
      if (Math.random() > 0.7) {
        const fromAgent = agentIds[Math.floor(Math.random() * agentIds.length)];
        const toAgent = agentIds[Math.floor(Math.random() * agentIds.length)];
        if (fromAgent !== toAgent) {
          setCommunicationLog((prev) => [
            {
              id: Date.now() + Math.random(),
              from: fromAgent,
              to: toAgent,
              message: `Task coordination: ${fromAgent} → ${toAgent}`,
              timestamp: Date.now(),
              type: "coordination",
            },
            ...prev.slice(0, 99),
          ]);
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Draw agent network visualization
  useEffect(() => {
    if (!svgRef.current || collapsed) return;

    const svg = svgRef.current;
    const rect = svg.getBoundingClientRect();
    const width = rect.width || 400;
    const height = rect.height || 300;

    // Clear previous content
    svg.innerHTML = "";

    // Create SVG namespace helper
    const createSVGElement = (tag, attributes = {}) => {
      const element = document.createElementNS(
        "http://www.w3.org/2000/svg",
        tag
      );
      Object.entries(attributes).forEach(([key, value]) => {
        element.setAttribute(key, value);
      });
      return element;
    };

    // Draw connections between agents
    const drawConnections = () => {
      communicationLog.slice(0, 10).forEach((comm, index) => {
        const fromAgent = agentDefinitions[comm.from];
        const toAgent = agentDefinitions[comm.to];

        if (fromAgent && toAgent) {
          const fromX = (fromAgent.position.x / 100) * width;
          const fromY = (fromAgent.position.y / 100) * height;
          const toX = (toAgent.position.x / 100) * width;
          const toY = (toAgent.position.y / 100) * height;

          const line = createSVGElement("line", {
            x1: fromX,
            y1: fromY,
            x2: toX,
            y2: toY,
            stroke: "#00ff41",
            "stroke-width": Math.max(1, 3 - index * 0.3),
            opacity: Math.max(0.1, 1 - index * 0.1),
            "stroke-dasharray": "2,2",
          });

          svg.appendChild(line);

          // Add animated pulse
          const animate = createSVGElement("animate", {
            attributeName: "opacity",
            values: `${0.8 - index * 0.1};${0.1};${0.8 - index * 0.1}`,
            dur: "2s",
            repeatCount: "indefinite",
          });
          line.appendChild(animate);
        }
      });
    };

    // Draw agent nodes
    const drawAgents = () => {
      Object.entries(agentDefinitions).forEach(([agentId, agent]) => {
        const state = agentStates[agentId];
        if (!state) return;

        const x = (agent.position.x / 100) * width;
        const y = (agent.position.y / 100) * height;
        const radius = 15;

        // Agent circle
        const circle = createSVGElement("circle", {
          cx: x,
          cy: y,
          r: radius,
          fill: agent.color,
          stroke: state.status === "active" ? "#00ff41" : "#666",
          "stroke-width": state.status === "active" ? 3 : 1,
          opacity: state.status === "error" ? 0.5 : 0.8,
        });

        svg.appendChild(circle);

        // Activity indicator
        if (state.status === "active" || state.status === "busy") {
          const pulse = createSVGElement("circle", {
            cx: x,
            cy: y,
            r: radius + 5,
            fill: "none",
            stroke: agent.color,
            "stroke-width": 2,
            opacity: 0.5,
          });

          const pulseAnimate = createSVGElement("animate", {
            attributeName: "r",
            values: `${radius + 5};${radius + 15};${radius + 5}`,
            dur: "1.5s",
            repeatCount: "indefinite",
          });
          pulse.appendChild(pulseAnimate);

          svg.appendChild(pulse);
        }

        // Agent label
        const text = createSVGElement("text", {
          x: x,
          y: y + radius + 15,
          "text-anchor": "middle",
          fill: "#c0c0c0",
          "font-size": "10px",
          "font-family": "Share Tech Mono, monospace",
        });
        text.textContent = agent.name;
        svg.appendChild(text);
      });
    };

    drawConnections();
    drawAgents();
  }, [agentStates, communicationLog, collapsed]);

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "success";
      case "busy":
        return "warning";
      case "error":
        return "error";
      case "completed":
        return "info";
      default:
        return "default";
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  if (collapsed) {
    return (
      <Card
        sx={{
          minHeight: 60,
          backgroundColor: "var(--soviet-panel)",
          border: "1px solid var(--soviet-brass)",
        }}>
        <CardContent sx={{ p: 1, textAlign: "center" }}>
          <Typography variant="caption" sx={{ color: "var(--soviet-brass)" }}>
            AGENT SWARM
          </Typography>
          <Box
            sx={{ display: "flex", justifyContent: "center", gap: 0.5, mt: 1 }}>
            {Object.entries(agentStates).map(([agentId, state]) => (
              <Box
                key={agentId}
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor:
                    state.status === "active"
                      ? "#00ff41"
                      : state.status === "busy"
                      ? "#ffb74d"
                      : state.status === "error"
                      ? "#f44336"
                      : "#666",
                }}
              />
            ))}
          </Box>
          <MechanicalButton
            onClick={onToggleCollapsed}
            size="small"
            style={{ fontSize: "10px", padding: "2px 6px", marginTop: "4px" }}>
            Expand
          </MechanicalButton>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      sx={{
        backgroundColor: "var(--soviet-panel)",
        border: "1px solid var(--soviet-brass)",
        borderRadius: "4px",
      }}>
      <CardContent>
        {/* Header */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 2,
          }}>
          <Typography
            variant="h6"
            sx={{ color: "var(--soviet-brass)", fontFamily: "Orbitron" }}>
            🎯 AGENT ORCHESTRATION COMMAND
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            <MechanicalButton
              onClick={() => window.location.reload()}
              size="small"
              variant="default">
              <Refresh />
            </MechanicalButton>
            <MechanicalButton
              onClick={onToggleCollapsed}
              size="small"
              variant="default">
              Collapse
            </MechanicalButton>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {/* Agent Activity Matrix */}
          <Grid item xs={12} md={6}>
            <Paper
              sx={{
                p: 2,
                backgroundColor: "var(--soviet-bg)",
                border: "1px solid #444",
              }}>
              <Typography
                variant="subtitle1"
                sx={{ color: "var(--soviet-amber)", mb: 2 }}>
                🤖 Agent Activity Matrix
              </Typography>

              <List dense>
                {Object.entries(agentDefinitions).map(([agentId, agent]) => {
                  const state = agentStates[agentId] || {};
                  return (
                    <ListItem key={agentId} sx={{ px: 0 }}>
                      <ListItemIcon>
                        <Badge
                          badgeContent={state.messagesProcessed}
                          color={getStatusColor(state.status)}
                          max={99}>
                          <Avatar
                            sx={{
                              width: 32,
                              height: 32,
                              backgroundColor: agent.color,
                              fontSize: "16px",
                            }}>
                            {agent.icon}
                          </Avatar>
                        </Badge>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}>
                            <Typography
                              variant="body2"
                              sx={{ fontWeight: "bold", color: agent.color }}>
                              {agent.name}
                            </Typography>
                            <Chip
                              size="small"
                              label={state.status?.toUpperCase() || "IDLE"}
                              color={getStatusColor(state.status)}
                              variant="outlined"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography
                              variant="caption"
                              sx={{ color: "var(--soviet-silver)" }}>
                              {state.task || agent.description}
                            </Typography>
                            {state.progress > 0 && (
                              <LinearProgress
                                variant="determinate"
                                value={state.progress}
                                sx={{ mt: 0.5, height: 4 }}
                              />
                            )}
                            <Box sx={{ display: "flex", gap: 2, mt: 0.5 }}>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 0.5,
                                }}>
                                <Speed
                                  sx={{
                                    fontSize: 12,
                                    color: "var(--soviet-green)",
                                  }}
                                />
                                <Typography variant="caption">
                                  CPU: {state.cpuUsage?.toFixed(1)}%
                                </Typography>
                              </Box>
                              <Box
                                sx={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 0.5,
                                }}>
                                <Memory
                                  sx={{
                                    fontSize: 12,
                                    color: "var(--soviet-amber)",
                                  }}
                                />
                                <Typography variant="caption">
                                  MEM: {state.memoryUsage?.toFixed(1)}%
                                </Typography>
                              </Box>
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  );
                })}
              </List>
            </Paper>
          </Grid>

          {/* Swarm Network Visualization */}
          <Grid item xs={12} md={6}>
            <Paper
              sx={{
                p: 2,
                backgroundColor: "var(--soviet-bg)",
                border: "1px solid #444",
              }}>
              <Typography
                variant="subtitle1"
                sx={{ color: "var(--soviet-amber)", mb: 2 }}>
                🕸️ Swarm Network Topology
              </Typography>

              <Box
                sx={{ position: "relative", height: 250, overflow: "hidden" }}>
                <svg
                  ref={svgRef}
                  width="100%"
                  height="100%"
                  style={{
                    backgroundColor: "#0a0a0a",
                    border: "1px solid #333",
                    borderRadius: "4px",
                  }}
                />
              </Box>

              {/* Network Metrics */}
              <Box
                sx={{ display: "flex", justifyContent: "space-around", mt: 2 }}>
                <Box sx={{ textAlign: "center" }}>
                  <NixieDisplay
                    value={networkMetrics.totalMessages}
                    label="Messages"
                  />
                </Box>
                <Box sx={{ textAlign: "center" }}>
                  <NixieDisplay
                    value={
                      Object.values(agentStates).filter(
                        (s) => s.status === "active"
                      ).length
                    }
                    label="Active"
                  />
                </Box>
                <Box sx={{ textAlign: "center" }}>
                  <NixieDisplay
                    value={networkMetrics.avgResponseTime}
                    label="Latency"
                  />
                </Box>
              </Box>
            </Paper>
          </Grid>

          {/* Communication Protocol Display */}
          <Grid item xs={12}>
            <Paper
              sx={{
                p: 2,
                backgroundColor: "var(--soviet-bg)",
                border: "1px solid #444",
              }}>
              <Typography
                variant="subtitle1"
                sx={{ color: "var(--soviet-amber)", mb: 2 }}>
                📡 Communication Protocol Log
              </Typography>

              <Box
                sx={{
                  height: 200,
                  overflow: "auto",
                  fontFamily: "Share Tech Mono",
                }}>
                {communicationLog.slice(0, 50).map((comm) => (
                  <Box
                    key={comm.id}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      py: 0.5,
                      borderBottom: "1px solid #333",
                      fontSize: "12px",
                    }}>
                    <Typography
                      variant="caption"
                      sx={{ color: "#666", minWidth: 60 }}>
                      {formatTimestamp(comm.timestamp)}
                    </Typography>
                    <Chip
                      size="small"
                      label={agentDefinitions[comm.from]?.name || comm.from}
                      sx={{ fontSize: "10px", height: 20 }}
                      color="primary"
                    />
                    <Router
                      sx={{ fontSize: 14, color: "var(--soviet-green)" }}
                    />
                    <Chip
                      size="small"
                      label={agentDefinitions[comm.to]?.name || comm.to}
                      sx={{ fontSize: "10px", height: 20 }}
                      color="secondary"
                    />
                    <Typography
                      variant="caption"
                      sx={{ color: "var(--soviet-silver)" }}>
                      {comm.message}
                    </Typography>
                  </Box>
                ))}

                {communicationLog.length === 0 && (
                  <Typography
                    variant="body2"
                    sx={{ color: "#666", textAlign: "center", py: 4 }}>
                    No agent communication detected. Start a workflow to see
                    real-time activity.
                  </Typography>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default AgentOrchestrationPanel;
