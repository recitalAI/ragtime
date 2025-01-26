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

      this.experimentData.items.forEach(item => {
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
          }
        }
      });

      const totalHallucinations = inventionCount + contradictionCount + corpusCount;

      return {
        totalQuestions,
        questionsWithHallucinations,
        totalFacts,
        totalHallucinations,
        hallucinationPercentage: ((questionsWithHallucinations / totalQuestions) * 100).toFixed(1),
        factsHallucinationPercentage: ((totalHallucinations / totalFacts) * 100).toFixed(1),
        inventionCount,
        contradictionCount,
        corpusCount,
        inventionPercentage: totalHallucinations > 0 ? ((inventionCount / totalHallucinations) * 100).toFixed(1) : '0.0',
        contradictionPercentage: totalHallucinations > 0 ? ((contradictionCount / totalHallucinations) * 100).toFixed(1) : '0.0',
        corpusPercentage: totalHallucinations > 0 ? ((corpusCount / totalHallucinations) * 100).toFixed(1) : '0.0',
        questionsInventionPercentage: ((questionsWithInvention / totalQuestions) * 100).toFixed(1),
        questionsContradictionPercentage: ((questionsWithContradiction / totalQuestions) * 100).toFixed(1),
        questionsCorpusPercentage: ((questionsWithCorpus / totalQuestions) * 100).toFixed(1)
      };
    },

    downloadReport() {
      try {
        const stats = this.calculateStats();
        const doc = new jsPDF();
        
        // Extract experiment name from the path parameter
        let experimentName = 'Experiment Report';
        const urlParams = new URLSearchParams(window.location.search);
        const path = urlParams.get('path');
        
        if (path) {
          experimentName = path.split('/').pop().replace('.json', '');
        }

        // Document setup with wider margins
        const pageWidth = doc.internal.pageSize.getWidth();
        const marginLeft = 15;
        const contentWidth = pageWidth - (marginLeft * 2);
        
        doc.setFont('helvetica');
        
        // Title
        doc.setFontSize(24);
        doc.setTextColor(44, 62, 80); // Dark blue
        doc.text(experimentName, marginLeft, 30);
        
        // Date
        doc.setFontSize(12);
        doc.setTextColor(127, 140, 141); // Gray
        doc.text(new Date().toLocaleDateString(), marginLeft, 40);
        
        // Horizontal line
        doc.setDrawColor(52, 152, 219); // Blue
        doc.setLineWidth(0.5);
        doc.line(marginLeft, 45, pageWidth - marginLeft, 45);
        
        // Reset text color
        doc.setTextColor(44, 62, 80);
        
        // Overview section
        doc.setFontSize(16);
        doc.text('Résumé', marginLeft, 60);
        
        doc.setFontSize(12);
        const p1 = `Sur ${stats.totalQuestions} questions, ${stats.questionsWithHallucinations} ont au moins une hallucination sur un des faits à vérifier, soit ${stats.hallucinationPercentage}% des questions.`;
        const p2 = `Au niveau des faits, ils ne sont que ${stats.totalHallucinations} sur ${stats.totalFacts}, soit ${stats.factsHallucinationPercentage}%.`;
        
        const p1Lines = doc.splitTextToSize(p1, contentWidth);
        const p2Lines = doc.splitTextToSize(p2, contentWidth);
        
        doc.text(p1Lines, marginLeft, 75);
        doc.text(p2Lines, marginLeft, 85);

        // Types of hallucinations section
        doc.setFontSize(16);
        doc.text('Types d\'hallucinations', marginLeft, 105);
        
        doc.setFontSize(12);
        
        // Define hallucination types with full descriptions
        const types = [
          {
            title: '[MISSING dans les Chunks] Invention :',
            desc: 'les chunks remontés ne contiennent pas l\'information, mais le LLM l\'ajoute.'
          },
          {
            title: '[Faits OK avec les Chunks] Contradiction :',
            desc: 'le LLM génère une information en contradiction avec les chunks remontés.'
          },
          {
            title: '[Chunks en HALLU avec les Faits] Corpus :',
            desc: 'une contradiction avec l\'un des faits est présente dans le corpus documentaire.'
          }
        ];

        let yPos = 120;
        types.forEach((type, index) => {
          // Write title
          doc.text(`${index + 1}. ${type.title}`, marginLeft, yPos);
          // Write description with proper wrapping
          const descLines = doc.splitTextToSize(type.desc, contentWidth - 10);
          doc.text(descLines, marginLeft + 5, yPos + 7);
          yPos += 20;
        });

        // Distribution section
        doc.setFontSize(16);
        doc.text('Distribution', marginLeft, yPos + 10);
        
        doc.setFontSize(12);
        const distributions = [
          `• Invention : ${stats.inventionCount}, soit ${stats.inventionPercentage}% des erreurs ou ${stats.questionsInventionPercentage}% des questions`,
          `• Contradiction : ${stats.contradictionCount}, soit ${stats.contradictionPercentage}% des erreurs ou ${stats.questionsContradictionPercentage}% des questions`,
          `• Corpus : ${stats.corpusCount}, soit ${stats.corpusPercentage}% des erreurs ou ${stats.questionsCorpusPercentage}% des questions`
        ];

        yPos += 25;
        distributions.forEach(dist => {
          const distLines = doc.splitTextToSize(dist, contentWidth);
          doc.text(distLines, marginLeft, yPos);
          yPos += 15;
        });

        // Footer with page numbers
        doc.setFontSize(10);
        doc.setTextColor(127, 140, 141);
        doc.text(
          `Page 1`, 
          pageWidth / 2, 
          doc.internal.pageSize.getHeight() - 10, 
          { align: 'center' }
        );

        // Save the PDF with experiment name
        doc.save(`${experimentName}_report.pdf`);
      } catch (error) {
        console.error('Error generating PDF:', error);
        this.downloadMarkdown();
      }
    },

    downloadMarkdown() {
      const stats = this.calculateStats();
      
      let experimentName = 'Experiment Report';
      const urlParams = new URLSearchParams(window.location.search);
      const path = urlParams.get('path');
      
      if (path) {
        experimentName = path.split('/').pop().replace('.json', '');
      }
      
      const content = `# ${experimentName}
${new Date().toLocaleDateString()}

## Résumé

Sur ${stats.totalQuestions} questions, ${stats.questionsWithHallucinations} ont au moins une hallucination sur un des faits à vérifier, soit ${stats.hallucinationPercentage}% des questions.

Au niveau des faits, ils ne sont que ${stats.totalHallucinations} sur ${stats.totalFacts}, soit ${stats.factsHallucinationPercentage}%.

## Types d'hallucinations

1. **[MISSING dans les Chunks] Invention :** Les chunks remontés ne contiennent pas l'information, mais le LLM l'ajoute.
2. **[Faits OK avec les Chunks] Contradiction :** Le LLM génère une information en contradiction avec les chunks remontés.
3. **[Chunks en HALLU avec les Faits] Corpus :** Une contradiction avec l'un des faits est présente dans le corpus documentaire.

## Distribution

- **Invention :** ${stats.inventionCount}, soit ${stats.inventionPercentage}% des erreurs ou ${stats.questionsInventionPercentage}% des questions
- **Contradiction :** ${stats.contradictionCount}, soit ${stats.contradictionPercentage}% des erreurs ou ${stats.questionsContradictionPercentage}% des questions
- **Corpus :** ${stats.corpusCount}, soit ${stats.corpusPercentage}% des erreurs ou ${stats.questionsCorpusPercentage}% des questions`;

      const blob = new Blob([content], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${experimentName}_report.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  }
};
</script>