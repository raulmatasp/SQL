import { io, Socket } from 'socket.io-client';

export interface CollaborationUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  cursor?: {
    x: number;
    y: number;
  };
  selection?: {
    start: number;
    end: number;
  };
}

export interface CollaborationEvent {
  type: 'user_joined' | 'user_left' | 'cursor_move' | 'text_change' | 'query_shared';
  user: CollaborationUser;
  data?: any;
  timestamp: Date;
}

export interface QueryCollaboration {
  queryId: string;
  content: string;
  participants: CollaborationUser[];
  lastModified: Date;
  version: number;
}

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;

  constructor() {
    this.connect();
  }

  private connect() {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    
    this.socket = io(wsUrl, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: this.reconnectInterval,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.handleReconnect();
    });
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        if (this.socket?.disconnected) {
          this.socket.connect();
        }
      }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts));
    }
  }

  // Collaboration features
  joinQuery(queryId: string, user: CollaborationUser) {
    if (!this.socket?.connected) return;

    this.socket.emit('join_query', { queryId, user });
  }

  leaveQuery(queryId: string) {
    if (!this.socket?.connected) return;

    this.socket.emit('leave_query', { queryId });
  }

  shareQuery(queryId: string, content: string, participants: string[]) {
    if (!this.socket?.connected) return;

    this.socket.emit('share_query', { queryId, content, participants });
  }

  updateQueryContent(queryId: string, content: string, cursor?: { start: number; end: number }) {
    if (!this.socket?.connected) return;

    this.socket.emit('query_update', { queryId, content, cursor });
  }

  updateCursor(queryId: string, position: { x: number; y: number }) {
    if (!this.socket?.connected) return;

    this.socket.emit('cursor_update', { queryId, position });
  }

  // Event listeners
  onUserJoined(callback: (user: CollaborationUser) => void) {
    if (!this.socket) return;
    this.socket.on('user_joined', callback);
  }

  onUserLeft(callback: (userId: string) => void) {
    if (!this.socket) return;
    this.socket.on('user_left', callback);
  }

  onQueryUpdate(callback: (update: { queryId: string; content: string; userId: string }) => void) {
    if (!this.socket) return;
    this.socket.on('query_updated', callback);
  }

  onCursorUpdate(callback: (update: { userId: string; position: { x: number; y: number } }) => void) {
    if (!this.socket) return;
    this.socket.on('cursor_updated', callback);
  }

  onQueryShared(callback: (query: QueryCollaboration) => void) {
    if (!this.socket) return;
    this.socket.on('query_shared', callback);
  }

  // Real-time notifications
  sendNotification(type: string, message: string, recipients: string[]) {
    if (!this.socket?.connected) return;

    this.socket.emit('notification', { type, message, recipients });
  }

  onNotification(callback: (notification: { type: string; message: string; sender: string }) => void) {
    if (!this.socket) return;
    this.socket.on('notification', callback);
  }

  // Query execution status
  subscribeToQueryExecution(queryId: string) {
    if (!this.socket?.connected) return;

    this.socket.emit('subscribe_query_execution', { queryId });
  }

  onQueryExecutionUpdate(callback: (update: { queryId: string; status: string; progress?: number; result?: any }) => void) {
    if (!this.socket) return;
    this.socket.on('query_execution_update', callback);
  }

  // Presence awareness
  updatePresence(status: 'active' | 'idle' | 'away', activity?: string) {
    if (!this.socket?.connected) return;

    this.socket.emit('presence_update', { status, activity });
  }

  onPresenceUpdate(callback: (update: { userId: string; status: string; activity?: string }) => void) {
    if (!this.socket) return;
    this.socket.on('presence_updated', callback);
  }

  // Chat functionality
  sendMessage(queryId: string, message: string) {
    if (!this.socket?.connected) return;

    this.socket.emit('chat_message', { queryId, message });
  }

  onMessage(callback: (message: { queryId: string; userId: string; message: string; timestamp: Date }) => void) {
    if (!this.socket) return;
    this.socket.on('chat_message', callback);
  }

  // Connection management
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Remove event listeners
  off(event: string, callback?: Function) {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  // Get connection status
  getConnectionStatus(): 'connected' | 'connecting' | 'disconnected' {
    if (!this.socket) return 'disconnected';
    if (this.socket.connected) return 'connected';
    return 'connecting';
  }
}

// Singleton instance
export const websocketService = new WebSocketService();

// React hooks for WebSocket functionality
export const useCollaboration = (queryId: string, user: CollaborationUser) => {
  const [participants, setParticipants] = React.useState<CollaborationUser[]>([]);
  const [messages, setMessages] = React.useState<any[]>([]);
  const [isConnected, setIsConnected] = React.useState(false);

  React.useEffect(() => {
    // Join query collaboration
    websocketService.joinQuery(queryId, user);

    // Set up event listeners
    websocketService.onUserJoined((newUser) => {
      setParticipants(prev => [...prev, newUser]);
    });

    websocketService.onUserLeft((userId) => {
      setParticipants(prev => prev.filter(p => p.id !== userId));
    });

    websocketService.onMessage((message) => {
      if (message.queryId === queryId) {
        setMessages(prev => [...prev, message]);
      }
    });

    const checkConnection = () => {
      setIsConnected(websocketService.isConnected());
    };

    const interval = setInterval(checkConnection, 1000);
    checkConnection();

    return () => {
      websocketService.leaveQuery(queryId);
      clearInterval(interval);
    };
  }, [queryId, user]);

  return {
    participants,
    messages,
    isConnected,
    sendMessage: (message: string) => websocketService.sendMessage(queryId, message),
    updateContent: (content: string, cursor?: { start: number; end: number }) =>
      websocketService.updateQueryContent(queryId, content, cursor),
    updateCursor: (position: { x: number; y: number }) =>
      websocketService.updateCursor(queryId, position),
  };
};

export default websocketService;