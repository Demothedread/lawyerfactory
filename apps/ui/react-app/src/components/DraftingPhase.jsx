import from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    AlertCircle,
    CheckCircle,
    Download,
    FileText,
    Loader2,
    Play,
    RefreshCw
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { generateSkeletalOutline, getClaimsMatrix, getSocket, startPhase } from '../services/apiService';
import ComplaintViewer from './ComplaintViewer';
import StatementOfFactsViewer from './StatementOfFactsViewer';

/**
 * DraftingPhase - Complete drafting workflow component
 * Integrates skeletal outline generation, drafting execution, and document viewing
 */
const DraftingPhase = ({ caseId, onPhaseComplete }) => {
  const [phaseState, setPhaseState] = useState({
    status: 'idle', // idle, generating_outline, drafting, completed, error
    progress: 0,
    currentStep: '',
    error: null
  });

  const [documents, setDocuments] = useState({
    skeletalOutline: null,
    statementOfFacts: null,
    complaint: null
  });

  const [claimsMatrix, setClaimsMatrix] = useState([]);
  const [activeTab, setActiveTab] = useState('outline');

  // Socket.IO event handlers
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const handlePhaseUpdate = (data) => {
      if (data.phase === 'phaseB02_drafting' && data.case_id === caseId) {
        setPhaseState(prev => ({
          ...prev,
          status: data.status,
          progress: data.progress || 0,
          currentStep: data.step || '',
          error: data.error || null
        }));

        // Update documents when they're generated
        if (data.documents) {
          setDocuments(prev => ({
            ...prev,
            ...data.documents
          }));
        }

        if (data.status === 'completed') {
          onPhaseComplete && onPhaseComplete(data);
        }
      }
    };

    socket.on('phase_progress_update', handlePhaseUpdate);

    return () => {
      socket.off('phase_progress_update', handlePhaseUpdate);
    };
  }, [caseId, onPhaseComplete]);

  // Load claims matrix on mount
  useEffect(() => {
    const loadClaimsMatrix = async () => {
      try {
        const matrix = await getClaimsMatrix(caseId);
        setClaimsMatrix(matrix);
      } catch (error) {
        console.error('Failed to load claims matrix:', error);
      }
    };

    if (caseId) {
      loadClaimsMatrix();
    }
  }, [caseId]);

  // Generate skeletal outline
  const handleGenerateOutline = useCallback(async () => {
    if (!claimsMatrix.length) {
      setPhaseState(prev => ({
        ...prev,
        error: 'No claims matrix available. Please complete research phase first.'
      }));
      return;
    }

    setPhaseState({
      status: 'generating_outline',
      progress: 0,
      currentStep: 'Generating skeletal outline...',
      error: null
    });

    try {
      const outlineData = await generateSkeletalOutline(caseId, claimsMatrix);
      setDocuments(prev => ({
        ...prev,
        skeletalOutline: outlineData
      }));

      setPhaseState(prev => ({
        ...prev,
        status: 'outline_generated',
        progress: 25,
        currentStep: 'Skeletal outline generated successfully'
      }));
    } catch (error) {
      setPhaseState(prev => ({
        ...prev,
        status: 'error',
        error: error.message || 'Failed to generate skeletal outline'
      }));
    }
  }, [caseId, claimsMatrix]);

  // Start drafting phase
  const handleStartDrafting = useCallback(async () => {
    if (!documents.skeletalOutline) {
      setPhaseState(prev => ({
        ...prev,
        error: 'Please generate skeletal outline first.'
      }));
      return;
    }

    setPhaseState({
      status: 'drafting',
      progress: 25,
      currentStep: 'Starting drafting phase...',
      error: null
    });

    try {
      await startPhase('phaseB02_drafting', caseId, {
        skeletal_outline: documents.skeletalOutline,
        claims_matrix: claimsMatrix
      });
    } catch (error) {
      setPhaseState(prev => ({
        ...prev,
        status: 'error',
        error: error.message || 'Failed to start drafting phase'
      }));
    }
  }, [caseId, documents.skeletalOutline, claimsMatrix]);

  // Handle document downloads
  const handleDownloadDocument = useCallback((docType) => {
    const doc = documents[docType];
    if (!doc) return;

    const blob = new Blob([JSON.stringify(doc, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${docType}_${caseId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [documents, caseId]);

  // Handle fact clicks in statement of facts
  const handleFactClick = useCallback((factId, evidence) => {
    console.log('Fact clicked:', factId, evidence);
    // Could open evidence viewer or highlight related content
  }, []);

  // Handle section editing in complaint
  const handleSectionEdit = useCallback((sectionId, content) => {
    console.log('Section edit requested:', sectionId, content);
    // Could open edit modal or trigger regeneration
  }, []);

  // Handle citation validation
  const handleValidateCitation = useCallback(async (citationId) => {
    // Mock validation - in real implementation, call API
    return { valid: Math.random() > 0.3 };
  }, []);

  // Render status indicator
  const renderStatusIndicator = () => {
    const { status, progress, currentStep, error } = phaseState;

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {status === 'idle' && <FileText className="w-4 h-4 text-gray-400" />}
            {status === 'generating_outline' && <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />}
            {status === 'drafting' && <Play className="w-4 h-4 text-green-500" />}
            {status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
            {status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
            <span className="text-sm font-medium capitalize">{status.replace('_', ' ')}</span>
          </div>
          <Badge variant="outline">{progress}%</Badge>
        </div>

        <Progress value={progress} className="w-full" />

        {currentStep && (
          <p className="text-xs text-gray-600">{currentStep}</p>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">{error}</AlertDescription>
          </Alert>
        )}
      </div>
    );
  };

  // Render skeletal outline preview
  const renderSkeletalOutline = () => {
    const outline = documents.skeletalOutline;
    if (!outline) {
      return (
        <div className="text-center py-8 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No skeletal outline generated yet.</p>
          <Button
            onClick={handleGenerateOutline}
            disabled={phaseState.status === 'generating_outline'}
            className="mt-4"
          >
            {phaseState.status === 'generating_outline' ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate Outline'
            )}
          </Button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">Skeletal Outline</h3>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerateOutline}
              disabled={phaseState.status === 'generating_outline'}
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Regenerate
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownloadDocument('skeletalOutline')}
            >
              <Download className="w-4 h-4 mr-1" />
              Download
            </Button>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <pre className="text-sm whitespace-pre-wrap font-mono">
            {typeof outline === 'string' ? outline : JSON.stringify(outline, null, 2)}
          </pre>
        </div>

        <div className="flex justify-end">
          <Button
            onClick={handleStartDrafting}
            disabled={phaseState.status === 'drafting'}
          >
            {phaseState.status === 'drafting' ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Drafting...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Start Drafting
              </>
            )}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Drafting Phase (B02)
        </CardTitle>
        <p className="text-sm text-gray-600">
          Generate skeletal outlines from claims matrix and produce professional legal documents
        </p>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Status and Progress */}
        {renderStatusIndicator()}

        <Separator />

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="outline">Skeletal Outline</TabsTrigger>
            <TabsTrigger value="facts" disabled={!documents.statementOfFacts}>
              Statement of Facts
            </TabsTrigger>
            <TabsTrigger value="complaint" disabled={!documents.complaint}>
              Complaint
            </TabsTrigger>
          </TabsList>

          <TabsContent value="outline" className="mt-4">
            {renderSkeletalOutline()}
          </TabsContent>

          <TabsContent value="facts" className="mt-4">
            <StatementOfFactsViewer
              caseId={caseId}
              documentData={documents.statementOfFacts}
              onFactClick={handleFactClick}
              onDownload={() => handleDownloadDocument('statementOfFacts')}
            />
          </TabsContent>

          <TabsContent value="complaint" className="mt-4">
            <ComplaintViewer
              caseId={caseId}
              documentData={documents.complaint}
              onSectionEdit={handleSectionEdit}
              onDownload={() => handleDownloadDocument('complaint')}
              onValidate={handleValidateCitation}
            />
          </TabsContent>
        </Tabs>

        {/* Claims Matrix Summary */}
        {claimsMatrix.length > 0 && (
          <>
            <Separator />
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-sm text-blue-800 mb-2">
                Claims Matrix Summary
              </h4>
              <div className="flex flex-wrap gap-2">
                {claimsMatrix.slice(0, 5).map((claim, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {claim.title || `Claim ${index + 1}`}
                  </Badge>
                ))}
                {claimsMatrix.length > 5 && (
                  <Badge variant="outline" className="text-xs">
                    +{claimsMatrix.length - 5} more
                  </Badge>
                )}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default DraftingPhase;