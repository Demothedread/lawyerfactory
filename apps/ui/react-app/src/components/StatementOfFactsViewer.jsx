import from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Download, FileText, Link, Search } from 'lucide-react';
import { useState } from 'react';

/**
 * StatementOfFactsViewer - React component for viewing generated Statement of Facts
 * Displays the generated statement of facts with fact-evidence mapping and interactive features
 */
const StatementOfFactsViewer = ({ caseId, documentData, onFactClick, onDownload }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedFacts, setHighlightedFacts] = useState(new Set());

  // Parse document data if it's a string
  const parsedData = typeof documentData === 'string' ? JSON.parse(documentData) : documentData;

  const {
    content = '',
    facts = [],
    evidence_mapping = {},
    metadata = {}
  } = parsedData || {};

  // Filter facts based on search term
  const filteredFacts = facts.filter(fact =>
    fact.text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    fact.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Handle fact highlighting
  const handleFactClick = (factId) => {
    const newHighlighted = new Set(highlightedFacts);
    if (newHighlighted.has(factId)) {
      newHighlighted.delete(factId);
    } else {
      newHighlighted.add(factId);
    }
    setHighlightedFacts(newHighlighted);

    if (onFactClick) {
      onFactClick(factId, evidence_mapping[factId]);
    }
  };

  // Render fact with highlighting
  const renderFact = (fact) => {
    const isHighlighted = highlightedFacts.has(fact.id);
    return (
      <div
        key={fact.id}
        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
          isHighlighted ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'
        }`}
        onClick={() => handleFactClick(fact.id)}
      >
        <div className="flex items-start justify-between mb-2">
          <Badge variant="outline" className="text-xs">
            {fact.category || 'Fact'}
          </Badge>
          {evidence_mapping[fact.id] && (
            <Badge variant="secondary" className="text-xs">
              <Link className="w-3 h-3 mr-1" />
              Evidence Linked
            </Badge>
          )}
        </div>
        <p className="text-sm text-gray-700">{fact.text}</p>
        {fact.source && (
          <p className="text-xs text-gray-500 mt-1">Source: {fact.source}</p>
        )}
      </div>
    );
  };

  return (
    <Card className="w-full h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Statement of Facts
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
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search facts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-96">
          {/* Facts List */}
          <div className="space-y-2">
            <h3 className="font-medium text-sm text-gray-700 mb-2">
              Key Facts ({filteredFacts.length})
            </h3>
            <ScrollArea className="h-full">
              <div className="space-y-2 pr-2">
                {filteredFacts.length > 0 ? (
                  filteredFacts.map(renderFact)
                ) : (
                  <p className="text-sm text-gray-500 text-center py-4">
                    {searchTerm ? 'No facts match your search.' : 'No facts available.'}
                  </p>
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Document Content */}
          <div className="space-y-2">
            <h3 className="font-medium text-sm text-gray-700 mb-2">
              Document Content
            </h3>
            <ScrollArea className="h-full">
              <div className="pr-2">
                {content ? (
                  <div className="prose prose-sm max-w-none">
                    {content.split('\n').map((paragraph, index) => (
                      <p key={index} className="mb-3 text-sm leading-relaxed">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No document content available.
                  </p>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* Statistics */}
        <Separator />
        <div className="flex justify-between text-xs text-gray-500">
          <span>Total Facts: {facts.length}</span>
          <span>Evidence Links: {Object.keys(evidence_mapping).length}</span>
          <span>Highlighted: {highlightedFacts.size}</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default StatementOfFactsViewer;