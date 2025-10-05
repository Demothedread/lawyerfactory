import from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, CheckCircle, ChevronDown, ChevronRight, Download, Edit, FileText } from 'lucide-react';
import { useState } from 'react';

/**
 * ComplaintViewer - React component for viewing generated Complaint document
 * Displays the generated complaint with expandable causes of action, citations, and interactive features
 */
const ComplaintViewer = ({ caseId, documentData, onSectionEdit, onDownload, onValidate }) => {
  const [expandedSections, setExpandedSections] = useState(new Set());
  const [validationStatus, setValidationStatus] = useState({});

  // Parse document data if it's a string
  const parsedData = typeof documentData === 'string' ? JSON.parse(documentData) : documentData;

  const {
    content = '',
    causes_of_action = [],
    citations = [],
    parties = {},
    metadata = {}
  } = parsedData || {};

  // Toggle section expansion
  const toggleSection = (sectionId) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  // Handle section editing
  const handleSectionEdit = (sectionId, content) => {
    if (onSectionEdit) {
      onSectionEdit(sectionId, content);
    }
  };

  // Handle citation validation
  const handleValidateCitation = async (citationId) => {
    if (onValidate) {
      try {
        const result = await onValidate(citationId);
        setValidationStatus(prev => ({
          ...prev,
          [citationId]: result.valid ? 'valid' : 'invalid'
        }));
      } catch (error) {
        setValidationStatus(prev => ({
          ...prev,
          [citationId]: 'error'
        }));
      }
    }
  };

  // Render cause of action section
  const renderCauseOfAction = (coa, index) => {
    const sectionId = `coa-${index}`;
    const isExpanded = expandedSections.has(sectionId);

    return (
      <Collapsible key={sectionId} className="border rounded-lg">
        <CollapsibleTrigger
          className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
          onClick={() => toggleSection(sectionId)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-500" />
              )}
              <div>
                <h4 className="font-medium text-sm">{coa.title || `Cause of Action ${index + 1}`}</h4>
                <p className="text-xs text-gray-500">{coa.description || 'Legal claim details'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {coa.citations && coa.citations.length > 0 && (
                <Badge variant="outline" className="text-xs">
                  {coa.citations.length} citations
                </Badge>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleSectionEdit(sectionId, coa.content);
                }}
              >
                <Edit className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent className="px-4 pb-4">
          <div className="space-y-3">
            {/* IRAC Structure */}
            {coa.irac && (
              <div className="grid grid-cols-1 gap-3">
                {coa.irac.issue && (
                  <div className="bg-blue-50 p-3 rounded border-l-4 border-blue-400">
                    <h5 className="font-medium text-xs text-blue-800 mb-1">ISSUE</h5>
                    <p className="text-sm text-blue-700">{coa.irac.issue}</p>
                  </div>
                )}
                {coa.irac.rule && (
                  <div className="bg-green-50 p-3 rounded border-l-4 border-green-400">
                    <h5 className="font-medium text-xs text-green-800 mb-1">RULE</h5>
                    <p className="text-sm text-green-700">{coa.irac.rule}</p>
                  </div>
                )}
                {coa.irac.application && (
                  <div className="bg-yellow-50 p-3 rounded border-l-4 border-yellow-400">
                    <h5 className="font-medium text-xs text-yellow-800 mb-1">APPLICATION</h5>
                    <p className="text-sm text-yellow-700">{coa.irac.application}</p>
                  </div>
                )}
                {coa.irac.conclusion && (
                  <div className="bg-purple-50 p-3 rounded border-l-4 border-purple-400">
                    <h5 className="font-medium text-xs text-purple-800 mb-1">CONCLUSION</h5>
                    <p className="text-sm text-purple-700">{coa.irac.conclusion}</p>
                  </div>
                )}
              </div>
            )}

            {/* Citations */}
            {coa.citations && coa.citations.length > 0 && (
              <div>
                <h5 className="font-medium text-xs text-gray-700 mb-2">CITATIONS</h5>
                <div className="space-y-2">
                  {coa.citations.map((citation, citIndex) => (
                    <div key={citIndex} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm font-mono">{citation.text}</span>
                      <div className="flex items-center gap-2">
                        {validationStatus[citation.id] === 'valid' && (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        )}
                        {validationStatus[citation.id] === 'invalid' && (
                          <AlertCircle className="w-4 h-4 text-red-500" />
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleValidateCitation(citation.id)}
                        >
                          Validate
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Full Content */}
            {coa.content && (
              <div>
                <h5 className="font-medium text-xs text-gray-700 mb-2">FULL CONTENT</h5>
                <div className="prose prose-sm max-w-none bg-gray-50 p-3 rounded">
                  <p className="text-sm leading-relaxed m-0">{coa.content}</p>
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  };

  return (
    <Card className="w-full h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Complaint Document
          </CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onDownload}
              disabled={!content}
            >
              <Download className="w-4 h-4 mr-1" />
              Download
            </Button>
          </div>
        </div>
        {metadata.generated_at && (
          <p className="text-xs text-gray-500">
            Generated: {new Date(metadata.generated_at).toLocaleString()}
          </p>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Parties Information */}
        {parties && Object.keys(parties).length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            {parties.plaintiff && (
              <div>
                <h4 className="font-medium text-sm text-gray-700 mb-1">Plaintiff</h4>
                <p className="text-sm">{parties.plaintiff}</p>
              </div>
            )}
            {parties.defendant && (
              <div>
                <h4 className="font-medium text-sm text-gray-700 mb-1">Defendant</h4>
                <p className="text-sm">{parties.defendant}</p>
              </div>
            )}
          </div>
        )}

        {/* Causes of Action */}
        <div className="space-y-3">
          <h3 className="font-medium text-sm text-gray-700">
            Causes of Action ({causes_of_action.length})
          </h3>
          {causes_of_action.length > 0 ? (
            causes_of_action.map(renderCauseOfAction)
          ) : (
            <p className="text-sm text-gray-500 text-center py-4">
              No causes of action available.
            </p>
          )}
        </div>

        {/* Full Document Content */}
        {content && (
          <>
            <Separator />
            <div className="space-y-2">
              <h3 className="font-medium text-sm text-gray-700">Full Document</h3>
              <ScrollArea className="h-64">
                <div className="pr-2">
                  <div className="prose prose-sm max-w-none">
                    {content.split('\n\n').map((paragraph, index) => (
                      <p key={index} className="mb-3 text-sm leading-relaxed">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </div>
              </ScrollArea>
            </div>
          </>
        )}

        {/* Statistics */}
        <Separator />
        <div className="flex justify-between text-xs text-gray-500">
          <span>Causes of Action: {causes_of_action.length}</span>
          <span>Total Citations: {citations.length}</span>
          <span>Validated: {Object.values(validationStatus).filter(s => s === 'valid').length}</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default ComplaintViewer;