<template>
  <v-btn
    v-if="hasChunkEvaluation"
    color="primary"
    variant="outlined"
    class="ml-3"
    @click="downloadReport"
    rounded
  >
    <v-icon
      size="17"
      start
    >
      fas fa-download
    </v-icon>
    Download Report
  </v-btn>
</template>

<script>
import { jsPDF } from 'jspdf';
import DOMPurify from 'dompurify';

export default {
  name: 'DownloadReport',
  props: {
    experimentData: {
      type: Object,
      required: true
    }
  },

  computed: {
    hasChunkEvaluation() {
      return this.experimentData.items.some(item => 
        item.chunkEvaluations && item.chunkEvaluations.length > 0
      );
    }
  },

  methods: {
    calculateStats() {
      const totalQuestions = this.experimentData.items.length;
      let totalFacts = 0;
      let questionsWithHallucinations = 0;
      let inventionCount = 0;
      let contradictionCount = 0;
      let corpusCount = 0;
      let questionsWithInvention = 0;
      let questionsWithContradiction = 0;
      let questionsWithCorpus = 0;
      let hallucinationDetails = [];

      this.experimentData.items.forEach((item, questionIndex) => {
        if (item.facts) {
          totalFacts += item.facts.length;
        }

        const mainAnswer = item.answers[0];
        const hallucinatedFacts = mainAnswer.evaluation?.hallu || [];
        
        if (hallucinatedFacts.length > 0) {
          questionsWithHallucinations++;

          const halluEval = item.chunkEvaluations.find(e => 
            e.type === "Hallucinations Eval" || e.type === "Hallucination Eval");
          
          if (halluEval?.evaluation?.meta) {
            const nbMissing = halluEval.evaluation.meta.nb_missing || 0;
            const nbOk = halluEval.evaluation.meta.nb_ok || 0;
            const nbHallu = halluEval.evaluation.meta.nb_hallu || 0;

            inventionCount += nbMissing;
            contradictionCount += nbOk;
            corpusCount += nbHallu;

            if (nbMissing > 0) questionsWithInvention++;
            if (nbOk > 0) questionsWithContradiction++;
            if (nbHallu > 0) questionsWithCorpus++;

            hallucinationDetails.push({
              questionIndex: questionIndex + 1,
              question: item.question,
              answer: mainAnswer.text,
              facts: item.facts,
              hallucinatedFacts,
              evaluation: mainAnswer.evaluation,
              chunkEvals: item.chunkEvaluations,
              meta: {
                invention: nbMissing,
                contradiction: nbOk,
                corpus: nbHallu
              }
            });
          }
        }
      });

      const totalHallucinations = inventionCount + contradictionCount + corpusCount;

      return {
        totalQuestions,
        questionsWithHallucinations,
        totalFacts,
        totalHallucinations,
        inventionCount,
        contradictionCount,
        corpusCount,
        questionsWithInvention,
        questionsWithContradiction,
        questionsWithCorpus,
        hallucinationDetails,
        hallucinationPercentage: ((questionsWithHallucinations / totalQuestions) * 100).toFixed(1),
        inventionPercentage: ((questionsWithInvention / totalQuestions) * 100).toFixed(1),
        contradictionPercentage: ((questionsWithContradiction / totalQuestions) * 100).toFixed(1),
        corpusPercentage: ((questionsWithCorpus / totalQuestions) * 100).toFixed(1)
      };
    },

    processHtml(html) {
      if (!html) return '';
      
      // First sanitize the HTML
      const sanitizedHtml = DOMPurify.sanitize(html);
      
      // Create temporary div
      const temp = document.createElement('div');
      temp.innerHTML = sanitizedHtml;

      // Handle lists
      const listItems = temp.querySelectorAll('li');
      listItems.forEach((li, index) => {
        // Keep original numbering for ordered lists
        const parent = li.parentElement;
        const prefix = parent.tagName === 'OL' ? `${index + 1}. ` : '- ';
        li.textContent = `${prefix}${li.textContent.trim()}`;
      });

      // Add proper spacing after list items
      const lists = temp.querySelectorAll('ol, ul');
      lists.forEach(list => {
        list.innerHTML = list.innerHTML.replace(/<\/li>/g, '</li>\n');
      });

      // Handle paragraphs
      const paragraphs = temp.querySelectorAll('p');
      paragraphs.forEach(p => {
        p.innerHTML = p.innerHTML + '\n\n';
      });

      // Convert HTML to plain text and clean up
      let text = temp.innerText || temp.textContent;
      text = text.replace(/\n{3,}/g, '\n\n').trim();
      
      return text;
    },

    renderMultiPageText(doc, text, marginLeft, contentWidth, currentY, lineSpacing = 5, indent = 0) {
      const lines = doc.splitTextToSize(text, contentWidth - indent);
      let startIdx = 0;
      
      while (startIdx < lines.length) {
        const availableHeight = doc.internal.pageSize.getHeight() - currentY - 10;
        const linesPerPage = Math.floor(availableHeight / lineSpacing);
        const endIdx = Math.min(startIdx + linesPerPage, lines.length);
        const pageLines = lines.slice(startIdx, endIdx);
        
        doc.text(pageLines, marginLeft + indent, currentY);
        startIdx = endIdx;
        
        if (startIdx < lines.length) {
          doc.addPage();
          currentY = 30;
        } else {
          currentY += (pageLines.length * lineSpacing);
        }
      }
      
      return currentY;
    },

    generateFirstPage(doc, stats, experimentName) {
      const pageWidth = doc.internal.pageSize.getWidth();
      const marginLeft = 20;
      const contentWidth = pageWidth - (marginLeft * 2);
      let currentY = 25;

      // Title and date
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(28);
      doc.setTextColor(44, 62, 80);
      doc.text(experimentName, marginLeft, currentY);
      
      currentY += 12;
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(11);
      doc.setTextColor(127, 140, 141);
      doc.text(new Date().toLocaleDateString(), marginLeft, currentY);
      
      // Summary section
      currentY += 15;
      doc.setTextColor(52, 73, 94);
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text('Résumé', marginLeft, currentY);
      
      currentY += 5;
      doc.setDrawColor(236, 240, 241);
      doc.setLineWidth(0.5);
      doc.line(marginLeft, currentY, pageWidth - marginLeft, currentY);
      
      currentY += 10;
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(11);
      doc.setTextColor(75, 75, 75);
      
      const summaryText = 
        `Sur ${stats.totalQuestions} questions, ${stats.questionsWithHallucinations} ont au moins ` +
        `une hallucination sur un des faits à vérifier, soit ${stats.hallucinationPercentage}% des questions.\n\n` +
        `Au niveau des faits, ils ne sont que ${stats.totalHallucinations} sur ${stats.totalFacts} faits.`;
      
      currentY = this.renderMultiPageText(doc, summaryText, marginLeft, contentWidth, currentY);
      
      // Types section
      currentY += 12;
      doc.setTextColor(52, 73, 94);
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text('Types d\'hallucinations', marginLeft, currentY);
      
      currentY += 5;
      doc.setDrawColor(236, 240, 241);
      doc.line(marginLeft, currentY, pageWidth - marginLeft, currentY);
      
      currentY += 10;
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(11);
      doc.setTextColor(75, 75, 75);
      
      const types = [
        {
          title: '[MISSING dans les Chunks] Invention',
          desc: 'les chunks remontés ne contiennent pas l\'information, mais le LLM l\'ajoute.'
        },
        {
          title: '[Faits OK avec les Chunks] Contradiction',
          desc: 'le LLM génère une information en contradiction avec les chunks remontés.'
        },
        {
          title: '[Chunks en HALLU avec les Faits] Corpus',
          desc: 'une contradiction avec l\'un des faits est présente dans le corpus documentaire.'
        }
      ];

      types.forEach((type, index) => {
        doc.setFont('helvetica', 'bold');
        const typeContent = `${index + 1}. ${type.title}`;
        currentY = this.renderMultiPageText(doc, typeContent, marginLeft, contentWidth, currentY);
        doc.setFont('helvetica', 'normal');
        currentY += 3;
        const descContent = `   ${type.desc}`;
        currentY = this.renderMultiPageText(doc, descContent, marginLeft, contentWidth, currentY);
        currentY += 5;
      });

      // Distribution section
      currentY += 12;
      doc.setTextColor(52, 73, 94);
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text('Distribution', marginLeft, currentY);
      
      currentY += 5;
      doc.setDrawColor(236, 240, 241);
      doc.line(marginLeft, currentY, pageWidth - marginLeft, currentY);
      
      currentY += 10;
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(11);
      doc.setTextColor(75, 75, 75);
      
      const distributionText = 
        `• Invention : ${stats.inventionCount}, soit ${stats.inventionPercentage}% des questions\n` +
        `• Contradiction : ${stats.contradictionCount}, soit ${stats.contradictionPercentage}% des questions\n` +
        `• Corpus : ${stats.corpusCount}, soit ${stats.corpusPercentage}% des questions`;
      
      currentY = this.renderMultiPageText(doc, distributionText, marginLeft, contentWidth, currentY);
    },

    generateDetailedAnalysis(doc, stats) {
      doc.addPage();
      const marginLeft = 20;
      const contentWidth = doc.internal.pageSize.getWidth() - (marginLeft * 2);
      const pageHeight = doc.internal.pageSize.getHeight();
      let currentY = 25;

      // Detailed Analysis Title
      doc.setTextColor(52, 73, 94);
      doc.setFontSize(22);
      doc.setFont('helvetica', 'bold');
      doc.text('Cas Détaillés des Hallucinations', marginLeft, currentY);
      
      // Add subtle section separator
      currentY += 5;
      doc.setDrawColor(236, 240, 241);
      doc.setLineWidth(0.5);
      doc.line(marginLeft, currentY, doc.internal.pageSize.getWidth() - marginLeft, currentY);
      
      currentY += 15;

      // Process each hallucination case
      for (const detail of stats.hallucinationDetails) {
          // Check if new page is needed - more space for question box
          if (currentY > pageHeight - 60) {
              doc.addPage();
              currentY = 25;
          }

          // Store starting Y position for frame
          const frameStartY = currentY;

          // Question title
          doc.setTextColor(52, 73, 94);
          doc.setFontSize(16);
          doc.setFont('helvetica', 'bold');
          const questionTitle = `Question ${detail.questionIndex}`;
          doc.text(questionTitle, marginLeft, currentY);
          currentY += 8; // Reduced from 10

          // Question text
          let questionEndY = currentY;
          if (detail.question) {
              doc.setTextColor(75, 75, 75);
              doc.setFontSize(11);
              doc.setFont('helvetica', 'normal');
              questionEndY = this.renderMultiPageText(doc, detail.question, marginLeft, contentWidth, currentY);
          }

          // Draw frame around question with more padding
          doc.setFillColor(248, 250, 252);
          doc.setDrawColor(226, 232, 240);
          doc.roundedRect(
              marginLeft - 5, 
              frameStartY - 8, // More top padding
              contentWidth + 10, 
              (questionEndY - frameStartY) + 10, // More bottom padding
              2, 
              2, 
              'FD'
          );

          // Re-draw text over frame
          doc.setTextColor(52, 73, 94);
          doc.setFontSize(16);
          doc.setFont('helvetica', 'bold');
          doc.text(questionTitle, marginLeft, frameStartY);

          if (detail.question) {
              doc.setTextColor(75, 75, 75);
              doc.setFontSize(11);
              doc.setFont('helvetica', 'normal');
              this.renderMultiPageText(doc, detail.question, marginLeft, contentWidth, frameStartY + 8);
          }

          currentY = questionEndY + 8; // Reduced spacing after question

          // Answer section
          if (detail.answer) {
              doc.setTextColor(52, 73, 94);
              doc.setFont('helvetica', 'bold');
              doc.setFontSize(11);
              doc.text('Réponse:', marginLeft, currentY);
              currentY += 6; // Reduced from 5
              
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(75, 75, 75);
              doc.setFontSize(10);
              
              const processedAnswer = this.processHtml(detail.answer);
              currentY = this.renderMultiPageText(doc, processedAnswer, marginLeft + 5, contentWidth - 5, currentY);
              currentY += 4; // Reduced from 8
          }

          // Facts section
          if (detail.facts?.length > 0) {
              doc.setTextColor(52, 73, 94);
              doc.setFont('helvetica', 'bold');
              doc.setFontSize(11);
              doc.text('Faits concernés:', marginLeft, currentY);
              currentY += 6; // Reduced from 5
              
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(75, 75, 75);
              doc.setFontSize(10);

              for (const fact of detail.facts) {
                  const isHallucinated = detail.hallucinatedFacts.includes(fact.text);
                  const prefix = isHallucinated ? '❌ ' : '✓ ';
                  const factContent = `${prefix}${fact.text}`;
                  
                  currentY = this.renderMultiPageText(doc, factContent, marginLeft + 5, contentWidth - 5, currentY);

                  if (isHallucinated && detail.evaluation?.text) {
                      doc.setTextColor(52, 73, 94);
                      const evalContent = `   Évaluation: ${detail.evaluation.text}`;
                      currentY = this.renderMultiPageText(doc, evalContent, marginLeft + 10, contentWidth - 10, currentY);
                      doc.setTextColor(52, 73, 94);
                    }
                  
                  currentY += 1.5; // Reduced from 3
              }
          }

          // Chunk evaluations
          if (detail.chunkEvals?.length > 0) {
              currentY += 4; // Reduced from 8
              doc.setTextColor(52, 73, 94);
              doc.setFont('helvetica', 'bold');
              doc.setFontSize(11);
              doc.text('Analyse détaillée des chunks:', marginLeft, currentY);
              currentY += 6; // Reduced from 5
              
              doc.setFont('helvetica', 'normal');
              doc.setTextColor(75, 75, 75);
              doc.setFontSize(10);

              for (const chunkEval of detail.chunkEvals) {
                  if (chunkEval.type === "Hallucinations Eval" || chunkEval.type === "Hallucination Eval") {
                      if (chunkEval.evaluation?.text) {
                          const evalText = this.processHtml(chunkEval.evaluation.text);
                          currentY = this.renderMultiPageText(doc, evalText, marginLeft + 5, contentWidth - 5, currentY);
                      }

                      const meta = chunkEval.evaluation?.meta;
                      if (meta) {
                          currentY += 1.5; // Reduced from 3
                          const metaContent = 
                              `- Chunks MISSING (Inventions) : ${meta.nb_missing || 0}\n` +
                              `- Faits OK avec Chunks (Contradictions) : ${meta.nb_ok || 0}\n` +
                              `- Chunks en HALLU avec Faits (Corpus) : ${meta.nb_hallu || 0}`;
                          
                          currentY = this.renderMultiPageText(doc, metaContent, marginLeft + 5, contentWidth - 5, currentY);
                      }
                  }
              }
          }

          // Add separator between questions with reduced spacing
          currentY += 4; // Reduced from 8
          doc.setDrawColor(236, 240, 241);
          doc.line(marginLeft, currentY, doc.internal.pageSize.getWidth() - marginLeft, currentY);
          currentY += 6; // Reduced from 12
      }
    },

    getExperimentName() {
      const urlParams = new URLSearchParams(window.location.search);
      const path = urlParams.get('path');
      return path ? path.split('/').pop().replace('.json', '') : 'Experiment Report';
    },

    async downloadReport() {
      try {
        const stats = this.calculateStats();
        const doc = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: 'a4'
        });
        
        const experimentName = this.getExperimentName();
        
        // Generate first page with summary
        this.generateFirstPage(doc, stats, experimentName);
        
        // Generate detailed analysis if there are hallucinations
        if (stats.hallucinationDetails.length > 0) {
          this.generateDetailedAnalysis(doc, stats);
        }

        // Add page numbers
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
          doc.setPage(i);
          doc.setFontSize(10);
          doc.setTextColor(127, 140, 141);
          doc.text(
            `Page ${i} / ${pageCount}`,
            doc.internal.pageSize.getWidth() / 2,
            doc.internal.pageSize.getHeight() - 10,
            { align: 'center' }
          );
        }

        // Save the PDF
        doc.save(`${experimentName}_report.pdf`);
      } catch (error) {
        console.error('Error generating PDF:', error);
      }
    }
  }
};
</script>

<style scoped>
.ml-3 {
  margin-left: 12px;
}
</style>