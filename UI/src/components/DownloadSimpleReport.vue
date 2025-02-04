// DownloadSimpleReport.vue
<template>
  <v-btn
    color="primary"
    variant="outlined"
    class="ml-3"
    @click="downloadReport"
    rounded
  >
    <v-icon size="17" start>fas fa-download</v-icon>
    Download Report
  </v-btn>
</template>

<script>
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import DOMPurify from 'dompurify';
import { formatDate } from '@/utils/dateFormatter';
import { marked } from 'marked';

// PDF Layout Manager Class
class PDFLayoutManager {
  constructor(doc) {
    this.doc = doc;
    this.pageHeight = doc.internal.pageSize.getHeight();
    this.pageWidth = doc.internal.pageSize.getWidth();
    this.marginLeft = 10;
    this.marginRight = 10;
    this.marginTop = 15;
    this.marginBottom = 25;
    this.contentWidth = this.pageWidth - this.marginLeft - this.marginRight;
    this.currentY = this.marginTop;
  }

  willContentFit(contentHeight) {
    return (this.currentY + contentHeight) <= (this.pageHeight - this.marginBottom);
  }

  addNewPage() {
    this.doc.addPage();
    this.currentY = this.marginTop;
    return this.currentY;
  }

  getRemainingSpace() {
    return this.pageHeight - this.marginBottom - this.currentY;
  }

  addContent(content, options = {}) {
    const {
      fontSize = 10,
      fontStyle = 'normal',
      spacing = 1,
      indent = 0,
      color = [0, 0, 0]
    } = options;

    this.doc.setFont('helvetica', fontStyle);
    this.doc.setFontSize(fontSize);
    this.doc.setTextColor(...color);

    const lines = this.doc.splitTextToSize(content, this.contentWidth - indent);
    const lineHeight = fontSize * spacing / 72 * 25.4;
    const totalHeight = lineHeight * lines.length;

    if (!this.willContentFit(totalHeight)) {
      const availableHeight = this.getRemainingSpace();
      const linesPerPage = Math.floor(availableHeight / lineHeight);
      
      const currentPageLines = lines.slice(0, linesPerPage);
      this.doc.text(currentPageLines, this.marginLeft + indent, this.currentY);
      
      this.addNewPage();
      const remainingLines = lines.slice(linesPerPage);
      if (remainingLines.length > 0) {
        this.doc.text(remainingLines, this.marginLeft + indent, this.currentY);
        this.currentY += lineHeight * remainingLines.length;
      }
    } else {
      this.doc.text(lines, this.marginLeft + indent, this.currentY);
      this.currentY += totalHeight;
    }

    this.doc.setTextColor(0, 0, 0); // Reset text color
    return this.currentY;
  }

  addTable(tableData, options = {}) {
    const estimatedHeight = (tableData.body.length) ;
    
    if (!this.willContentFit(estimatedHeight)) {
      this.addNewPage();
    }

    this.doc.autoTable({
      startY: this.currentY,
      margin: { left: this.marginLeft, right: this.marginRight },
      ...options,
      ...tableData
    });

    this.currentY = this.doc.lastAutoTable.finalY + 6;
    return this.currentY;
  }

  addSection(title, content, options = {}) {
    const headerHeight = 6;
    const spacingAfterHeader = 0;

    if (this.getRemainingSpace() < 10) {
      this.addNewPage();
    }

    this.doc.setFont('helvetica', 'bold');
    this.doc.setFontSize(12);
    this.doc.text(title, this.marginLeft, this.currentY);
    this.currentY += headerHeight + spacingAfterHeader;

    if (content) {
      return this.addContent(content, options);
    }
    return this.currentY;
  }

  addInfoBox(infoGrid) {
    const boxHeight = infoGrid.length * 4;

    if (!this.willContentFit(boxHeight)) {
      this.addNewPage();
    }

    this.doc.setDrawColor(220, 220, 220);
    this.doc.setFillColor(250, 250, 250);
    this.doc.roundedRect(
      this.marginLeft,
      this.currentY,
      this.contentWidth,
      boxHeight,
      2,
      2,
      'FD'
    );

    infoGrid.forEach(([label, value], idx) => {
      this.doc.setFont('helvetica', 'bold');
      this.doc.setFontSize(8);
      this.doc.text(label, this.marginLeft + 5, this.currentY + 3 + (idx * 4));
      
      this.doc.setFont('helvetica', 'normal');
      this.doc.text(value, this.marginLeft + 35, this.currentY + 3 + (idx * 4));
    });

    this.currentY += boxHeight + 5;
    return this.currentY;
  }
}

export default {
  name: 'DownloadSimpleReport',
  props: {
    experimentData: {
      type: Object,
      required: true
    }
  },

  methods: {
    formatAnswer(text) {
      const formattedText = text.replace(/([:.)\]])(nn?)/g, (match, p1, p2) => {
        return p1 + (p2 === 'nn' ? '\n\n' : '\n');
      });
      
      const markedText = marked(formattedText);
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = markedText;
      return tempDiv.textContent || tempDiv.innerText;
    },

    processData() {
      const mainResults = [];
      const models = [...new Set(this.experimentData.items.flatMap(item => 
        item.answers.map(answer => answer.model)
      ))];

      models.forEach(model => {
        const modelResults = {
          name: model,
          date: null,
          facts: 0,
          ok: 0,
          hallu: 0,
          missing: 0,
          extra: 0
        };

        this.experimentData.items.forEach(item => {
          const answer = item.answers.find(a => a.model === model);
          if (answer && answer.evaluation) {
            modelResults.date = answer.time;
            modelResults.facts += item.facts.length;
            modelResults.ok += (answer.evaluation.ok?.length || 0);
            modelResults.hallu += (answer.evaluation.hallu?.length || 0);
            modelResults.missing += (answer.evaluation.missing?.length || 0);
            modelResults.extra += (answer.evaluation.extra || 0);
          }
        });

        mainResults.push(modelResults);
      });

      const detailedResults = this.experimentData.items.map((item, index) => {
        const mainAnswer = item.answers[0];
        const evaluation = mainAnswer.evaluation || {};
        return this.processDetailedResult(item, index, mainAnswer, evaluation);
      });

      return { mainResults, detailedResults };
    },

    async downloadReport() {
      try {
        const { mainResults, detailedResults } = this.processData();
        const doc = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: 'a4'
        });

        const layoutManager = new PDFLayoutManager(doc);

        // Title
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(24);
        doc.text(this.getExperimentName(), layoutManager.marginLeft, layoutManager.currentY);
        layoutManager.currentY += 10;

        // Summary section
        layoutManager.addSection('Summary', '');
        layoutManager.addTable({
          head: [['Model', 'Date', 'Facts', 'Ok', 'Hallu', 'Missing', 'Extra']],
          body: mainResults.map(result => [
            result.name,
            formatDate(result.date),
            result.facts,
            `${this.calculatePercentage(result.ok, result.facts)}% (${result.ok}/${result.facts})`,
            `${this.calculatePercentage(result.hallu, result.facts)}% (${result.hallu}/${result.facts})`,
            `${this.calculatePercentage(result.missing, result.facts)}% (${result.missing}/${result.facts})`,
            result.extra
          ])
        }, {
          theme: 'grid',
          styles: { fontSize: 8, cellPadding: 2 },
          headStyles: { fillColor: [242, 242, 242], textColor: [0, 0, 0], fontStyle: 'bold' }
        });

        // Process each question
        for (const result of detailedResults) {
          // Question section
          layoutManager.addSection(`Question ${result.originalIndex}`, result.question);
          
          // Stats table
          layoutManager.addTable({
            head: [['Facts', 'OK', 'Hallu', 'Missing', 'Extra']],
            body: [[
              result.mainResult.factsCount,
              `${this.calculatePercentage(result.mainResult.ok, result.mainResult.factsCount)}% (${result.mainResult.ok}/${result.mainResult.factsCount})`,
              `${this.calculatePercentage(result.mainResult.hallu, result.mainResult.factsCount)}% (${result.mainResult.hallu}/${result.mainResult.factsCount})`,
              `${this.calculatePercentage(result.mainResult.missing, result.mainResult.factsCount)}% (${result.mainResult.missing}/${result.mainResult.factsCount})`,
              result.mainResult.extra
            ]]
          }, {
            theme: 'grid',
            styles: { fontSize: 8, cellPadding: 2 }
          });

          // Answer section
          layoutManager.addSection('Answer', '');
          layoutManager.addInfoBox([
            ['Model:', result.answerModel],
            ['Date:', formatDate(result.answerDate)],
            ['Duration:', `${result.answerDuration.toFixed(2)}s`],
            ['Cost:', this.formatCost(result.answerCost)]
          ]);
          layoutManager.addContent(result.answer, { spacing: 1.2 });

          // Evaluation section
          layoutManager.addSection('Evaluation', '');
          layoutManager.addInfoBox([
            ['Model:', result.evalModel],
            ['Date:', formatDate(result.evalDate)],
            ['Duration:', `${result.evalDuration.toFixed(2)}s`],
            ['Cost:', this.formatCost(result.evalCost)]
          ]);

          // Facts section
          layoutManager.addSection('Facts', '');
          for (const fact of result.facts) {
            
            // Status indicator
            this.setStatusColor(doc, fact.status);
            doc.circle(layoutManager.marginLeft + 2, layoutManager.currentY + 2, 1, 'F');
            
            // Fact text
            layoutManager.addContent(fact.text, { indent: 5 });

            // Evaluation text
            if (fact.evaluation) {
              const cleanEval = this.cleanHtml(fact.evaluation);
              layoutManager.addContent(cleanEval, {
                indent: 10,
                fontStyle: 'italic',
                fontSize: 8
              });
            }

            // Problem analysis
            if (fact.problemType && fact.problemExplanation) {
              const problemText = `${fact.problemType}: ${fact.problemExplanation}`;
              doc.setFillColor(253, 237, 237);
              const problemLines = doc.splitTextToSize(problemText, layoutManager.contentWidth - 30);
              const boxHeight = (problemLines.length * 5) + 8;
              
              if (!layoutManager.willContentFit(boxHeight)) {
                layoutManager.addNewPage();
              }
              
              doc.roundedRect(
                layoutManager.marginLeft + 10,
                layoutManager.currentY,
                layoutManager.contentWidth - 20,
                boxHeight,
                2,
                2,
                'F'
              );
              
              layoutManager.addContent(problemText, {
                indent: 15,
                color: [114, 28, 36],
                fontSize: 8
              });
            }

            // Chunk evaluation
            if (fact.chunkEvaluation) {
              layoutManager.addContent(fact.chunkEvaluation, {
                indent: 10,
                fontSize: 6
              });
            }

            // Chunk info
            if (fact.chunkInfo && fact.chunkInfo.length > 0) {
              fact.chunkInfo.forEach(chunk => {
                layoutManager.addContent(`Chunk ${chunk.number}: ${chunk.text}`, {
                  indent: 15,
                  fontSize: 6
                });
              });
            }

            layoutManager.currentY += 5;
          }
        }

        // Add page numbers
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
          doc.setPage(i);
          doc.setFont('helvetica', 'normal');
          doc.setFontSize(6);
          doc.setTextColor(100);
          doc.text(
            `Page ${i} of ${pageCount}`,
            layoutManager.pageWidth / 2,
            layoutManager.pageHeight - 5,
            { align: 'center' }
          );
        }

        doc.save(`${this.getExperimentName()}_report.pdf`);
      } catch (error) {
        console.error('Error generating PDF:', error);
      }
    },

    // Rest of your existing helper methods
    processDetailedResult(item, index, mainAnswer, evaluation) {
      return {
        originalIndex: index + 1,
        question: item.question,
        mainResult: {
          ok: evaluation.ok?.length || 0,
          hallu: evaluation.hallu?.length || 0,
          missing: evaluation.missing?.length || 0,
          extra: evaluation.extra || 0,
          score: evaluation.auto || 0,
          factsCount: item.facts.length
        },
        answer: this.formatAnswer(mainAnswer.text),
        answerModel: mainAnswer.model,
        answerDate: mainAnswer.time,
        answerDuration: mainAnswer.duration,
        answerCost: mainAnswer.cost,
        evalModel: evaluation.model,
        evalDate: evaluation.time,
        evalDuration: evaluation.duration,
        evalCost: evaluation.cost,
        facts: this.processFactsWithEvaluation(item.facts, evaluation, item.chunkEvaluations, item.chunks)
      };
    },

    processFactsWithEvaluation(facts, evaluation, chunkEvaluations, chunks) {
      return facts.map((fact, index) => {
        const factNumber = index + 1;
        const factEval = this.extractFactEvaluation(evaluation?.text, factNumber);
        const chunkEval = this.extractChunkEvaluation(chunkEvaluations, factNumber, chunks);
        
        const status = this.getFactStatus(factEval.result);
        const { problemType, explanation } = this.analyzeFactAndChunkStatus(status, chunkEval.status);

        return {
          text: fact.text,
          status,
          evaluation: factEval.evalShow,
          chunkEvaluation: chunkEval.evaluation,
          problemType,
          problemExplanation: explanation,
          chunkInfo: chunkEval.chunkButtons
        };
      });
    },

    extractFactEvaluation(evalText, factNumber) {
      if (!evalText) return { result: '', evalShow: '' };
      
      const cleanText = evalText.replace(/<\/?[^>]+(>|$)/g, "\n").replace(/\n+/g, "\n").trim();
      const textWithoutExtra = cleanText.split(/\[extra\]|\[EXTRA\]|<p>\s*\[?extra\]?/i)[0];

      const itemPattern = new RegExp(
        `(?:^|\\n)\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*` +
        `\\[(OK|NOT FOUND|HALLU)\\]` +
        `(?:(?!(?:\\n\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*\\[(OK|NOT FOUND|HALLU)\\])).)*`,
        'gms'
      );
      
      const paragraphPattern = new RegExp(
        `(?:Part(?:ie)? (?:in|dans) (?:the|le) paragraphe?|Citation pertinente du paragraphe|Part in the paragraph)\\s*(?::|:?\\s*)(.*)|(No part in the paragraph supports this fact\\.)`,
        'i'
      );

      try {
        let matches = [...(textWithoutExtra.matchAll(itemPattern) || [])];
        let result = '';
        
        if (matches.length > 0) {
          result = matches[factNumber - 1][0].trim();
          
          const patternToCheck = /(?:\n\s*(?:\d+\.|\[?\d+\]?)?\s*\[(OK|NOT FOUND|HALLU)\])/g;
          const occurrences = (result.match(patternToCheck) || []).length;
          
          if (occurrences > 1) {
            console.warn('Multiple fact patterns found in the result. Resetting matches.');
            matches = [];
            result = '';
          }
          
          if (result) {
            const stateMatch = result.match(/^\s*(?:\d+\.|\[\d+\])?\s*\[(OK|NOT FOUND|HALLU)\]/i);
            const state = stateMatch ? stateMatch[1] : '';
            
            let uniqueResult = result.replace(/^\s*(?:\d+\.|\[\d+\])?\s*\[(OK|NOT FOUND|HALLU)\]\s*-?\s*/i, '');
            const partMatch = result.match(paragraphPattern);
            let processedPartMatch = '';
            
            if (partMatch) {
              processedPartMatch = (partMatch[1] || partMatch[2] || '').trim();
              uniqueResult = uniqueResult.replace(partMatch[0], '').trim();
            }

            processedPartMatch = processedPartMatch.replace(/N\/A|None/gi, "").trim();
            const evalShow = `<p><em>${processedPartMatch || ' '}</em></p><p>${uniqueResult}</p>`;

            return { result: `[${state}] ${uniqueResult}`, evalShow };
          }
        }
      } catch (error) {
        console.warn('Error extracting fact evaluation:', error);
      }

      return { result: '', evalShow: '' };
    },

    extractChunkEvaluation(chunkEvals, factNumber, qaChunks) {
      if (!chunkEvals) {
        return { status: '', evaluation: '', chunkButtons: [] };
      }

      const relevantEval = chunkEvals.find(evalItem => 
        evalItem.evaluation?.text?.includes(`[Fait ${factNumber}]`)
      );

      if (relevantEval) {
        const regex = new RegExp(`\\[Fait ${factNumber}\\].*?(?=\\[Fait|$)`, 's');
        const match = relevantEval.evaluation.text.match(regex);
        const result = match ? match[0].trim() : '';

        const statusMatch = result.match(/(?:statut|status)\s*(?::)?\s*\[?(OK|HALLU|MISSING)\]?/i);
        const status = statusMatch ? statusMatch[1].toLowerCase() : '';

        const explanationMatch = result.match(/Explication : (.*?)(?=\nLes chunks|\nSource|$)/s);
        const explanation = explanationMatch ? explanationMatch[1].trim() : '';

        const sourceMatch = result.match(/Source(?:\s*\(si applicable\))?\s*(?::)?\s*"([^"]*)"/);
        const source = sourceMatch ? sourceMatch[1] : '';

        const chunksMatch = result.match(/Les chunks(?:\s*\(si applicable\))?\s*(?::)?\s*"([^"]*)"/);
        const chunks = chunksMatch ? chunksMatch[1] : '';
        const chunkNumbers = chunks.match(/\d+/g) || [];

        const chunkButtons = chunkNumbers.map(num => ({
          number: parseInt(num),
          text: qaChunks[parseInt(num) - 1]?.text || 'Chunk not found'
        }));

        const formattedEval = `${source ? `Source: ${source}\n` : ''}${explanation}`;

        return { status, evaluation: formattedEval, chunkButtons };
      }

      return { status: '', evaluation: '', chunkButtons: [] };
    },

    analyzeFactAndChunkStatus(factStatus, chunkStatus) {
      const statusMap = {
        'missingok': {
          type: 'LLM issue',
          explanation: 'Correct chunks retrieved but the LLM failed to generate the correct answer.'
        },
        'missingmissing': {
          type: 'Retriever or source issue',
          explanation: 'Chunks do not provide the correct context.'
        },
        'missinghallu': {
          type: 'Retriever or source issue',
          explanation: 'Chunks provide inconsistent context, LLM detected that and didn\'t answer.'
        },
        'halluok': {
          type: 'Contradiction',
          explanation: 'The LLM generates information that contradicts the information contained in the provided chunks.'
        },
        'hallumissing': {
          type: 'Invention',
          explanation: 'The chunks provided do not contain the information, but the LLM adds it.'
        },
        'halluhallu': {
          type: 'Corpus',
          explanation: 'A contradiction with one of the facts is present in the corpus.'
        }
      };

      const key = `${factStatus}${chunkStatus}`;
      const result = statusMap[key] || { type: '', explanation: '' };
      return {
        problemType: result.type,
        explanation: result.explanation
      };
    },

    getFactStatus(evalResult) {
      if (evalResult.includes('[OK]')) return 'ok';
      if (evalResult.includes('[NOT FOUND]')) return 'missing';
      if (evalResult.includes('[HALLU]')) return 'hallu';
      return 'unknown';
    },

    calculatePercentage(value, total) {
      if (total === 0) return '0.0';
      return ((value / total) * 100).toFixed(1);
    },

    formatCost(cost) {
      return `${(cost * 100).toFixed(2)}c$`;
    },

    getExperimentName() {
      const urlParams = new URLSearchParams(window.location.search);
      const path = urlParams.get('path');
      return path ? path.split('/').pop().replace('.json', '') : 'Experiment Report';
    },

    setStatusColor(doc, status) {
      switch (status) {
        case 'ok':
          doc.setFillColor(40, 167, 69); // Green
          break;
        case 'missing':
          doc.setFillColor(255, 193, 7); // Yellow
          break;
        case 'hallu':
          doc.setFillColor(220, 53, 69); // Red
          break;
        default:
          doc.setFillColor(108, 117, 125); // Gray
      }
    },

    cleanHtml(html) {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = DOMPurify.sanitize(html);
      return tempDiv.textContent || tempDiv.innerText;
    }
  }
};
</script>

<style scoped>
.ml-3 {
  margin-left: 12px;
}
</style>