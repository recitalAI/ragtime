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
// ── Design tokens ──────────────────────────────────────────────────────────
const RC = {
  ink:        [33, 37, 41],
  sub:        [108, 117, 125],
  hairline:   [226, 232, 235],
  brand:      [16, 163, 127],
  brandDark:  [12, 122, 96],
  brandFaint: [232, 247, 243],
  ok:         [34, 160, 84],
  okBg:       [233, 247, 238],
  hallu:      [220, 53, 69],
  halluBg:    [251, 236, 238],
  missing:    [230, 160, 12],
  missingBg:  [252, 246, 231],
  cardBg:     [248, 250, 251],
  cardBorder: [230, 235, 238],
  white:      [255, 255, 255],
  chunkBg:    [245, 247, 249],
};

// PDF Layout Manager — redesigned presentation. Same data in, nicer layout out.
class PDFLayoutManager {
  constructor(doc) {
    this.doc = doc;
    this.pageHeight = doc.internal.pageSize.getHeight();
    this.pageWidth = doc.internal.pageSize.getWidth();
    this.marginLeft = 16;
    this.marginRight = 16;
    this.marginTop = 18;
    this.marginBottom = 18;
    this.contentWidth = this.pageWidth - this.marginLeft - this.marginRight;
    this.currentY = this.marginTop;
  }

  // jsPDF's built-in Helvetica only covers Latin-1. Characters outside it
  // (typographic quotes, non-breaking hyphen, oe ligature, en dash…) make
  // splitTextToSize mis-measure widths, so text overflows the right margin and
  // renders with odd spacing. Normalize them to safe Latin-1 equivalents
  // before any text is measured or drawn. The non-breaking hyphen (U+2011) is
  // the worst offender: it also blocks line wrapping, so it maps to a normal
  // hyphen. NBSP -> normal space for the same reason.
  sanitize(text) {
    if (text === null || text === undefined) return '';
    return String(text)
      .replace(/[\u2018\u2019\u201A\u201B]/g, "'")   // single quotes/apostrophes
      .replace(/[\u201C\u201D\u201E\u201F]/g, '"')   // double quotes
      .replace(/\u2011/g, '-')                        // non-breaking hyphen
      .replace(/[\u2012\u2013\u2014\u2015]/g, '-')    // figure/en/em dashes
      .replace(/\u2026/g, '...')                      // ellipsis
      .replace(/\u00A0/g, ' ')                        // non-breaking space
      .replace(/\u0153/g, 'oe').replace(/\u0152/g, 'OE') // oe / OE ligatures
      .replace(/\u00E6/g, 'ae').replace(/\u00C6/g, 'AE') // ae / AE ligatures
      .replace(/[\u2022\u2023\u25E6]/g, '-')          // bullets
      .replace(/[\u200B-\u200D\uFEFF]/g, '');         // zero-width chars
  }

  // pt -> mm line height
  _lh(fontSize, spacing = 1.35) { return fontSize * spacing * 0.3528; }

  willContentFit(h) { return (this.currentY + h) <= (this.pageHeight - this.marginBottom); }
  getRemainingSpace() { return this.pageHeight - this.marginBottom - this.currentY; }

  addNewPage() { this.doc.addPage(); this.currentY = this.marginTop; return this.currentY; }
  ensure(h) { if (!this.willContentFit(h)) this.addNewPage(); }

  _set(size, style = 'normal', color = RC.ink) {
    this.doc.setFont('helvetica', style);
    this.doc.setFontSize(size);
    this.doc.setTextColor(...color);
  }

  // Wrapped paragraph that never splits a line across a page boundary.
  addContent(content, options = {}) {
    const { fontSize = 10, fontStyle = 'normal', spacing = 1.35, indent = 0, color = RC.ink, gapAfter = 0 } = options;
    if (content === null || content === undefined || content === '') { this.currentY += gapAfter; return this.currentY; }
    this._set(fontSize, fontStyle, color);
    const lines = this.doc.splitTextToSize(this.sanitize(content), this.contentWidth - indent);
    const lineH = this._lh(fontSize, spacing);
    for (const line of lines) {
      this.ensure(lineH);
      this.doc.text(line, this.marginLeft + indent, this.currentY);
      this.currentY += lineH;
    }
    this.currentY += gapAfter;
    this.doc.setTextColor(...RC.ink);
    return this.currentY;
  }

  addTable(tableData, options = {}) {
    // let autoTable handle page breaks; just make sure we're not at the very bottom
    if (this.getRemainingSpace() < 16) this.addNewPage();
    this.doc.autoTable({
      startY: this.currentY,
      margin: { left: this.marginLeft, right: this.marginRight },
      ...options,
      ...tableData,
    });
    this.currentY = this.doc.lastAutoTable.finalY + 5;
    return this.currentY;
  }

  hairline(gapBefore = 0, gapAfter = 0, color = RC.hairline) {
    this.currentY += gapBefore;
    this.ensure(1);
    this.doc.setDrawColor(...color);
    this.doc.setLineWidth(0.2);
    this.doc.line(this.marginLeft, this.currentY, this.pageWidth - this.marginRight, this.currentY);
    this.currentY += gapAfter;
  }

  // Green question banner: faint band + solid left bar + "QUESTION N" kicker.
  questionBanner(number, question) {
    this._set(12.5, 'bold', RC.ink);
    const qLines = this.doc.splitTextToSize(this.sanitize(question), this.contentWidth - 16);
    const qH = qLines.length * this._lh(12.5, 1.28);
    const bandH = Math.max(13, 8 + qH);
    this.ensure(bandH + 6);
    this.currentY += 2;
    this.doc.setFillColor(...RC.brandFaint);
    this.doc.roundedRect(this.marginLeft, this.currentY, this.contentWidth, bandH, 1.5, 1.5, 'F');
    this.doc.setFillColor(...RC.brand);
    this.doc.roundedRect(this.marginLeft, this.currentY, 2.4, bandH, 1.2, 1.2, 'F');
    this._set(7.5, 'bold', RC.brandDark);
    this.doc.text(`QUESTION ${number}`, this.marginLeft + 7, this.currentY + 5);
    this._set(12.5, 'bold', RC.ink);
    let ty = this.currentY + 10;
    for (const line of qLines) { this.doc.text(line, this.marginLeft + 7, ty); ty += this._lh(12.5, 1.28); }
    this.currentY += bandH + 5;
  }

  // Small dotted sub-header: "Answer" / "Evaluation" / "Facts".
  subHeader(label, accent = RC.brand) {
    this.ensure(9);
    this.currentY += 1.5;
    this.doc.setFillColor(...accent);
    this.doc.circle(this.marginLeft + 1.4, this.currentY - 1.1, 1.1, 'F');
    this._set(10.5, 'bold', RC.ink);
    this.doc.text(label, this.marginLeft + 5, this.currentY);
    this.currentY += 5;
  }

  // Compact one/two-row meta strip instead of the tall grey info box.
  metaStrip(items) {
    this.ensure(6);
    let x = this.marginLeft;
    const rowH = 4.6;
    for (const [rawLabel, rawValue] of items) {
      const label = this.sanitize(String(rawLabel).replace(/:$/, ''));
      const value = this.sanitize(rawValue === null || rawValue === undefined ? '-' : rawValue);
      this.doc.setFont('helvetica', 'bold'); this.doc.setFontSize(7.5);
      const lw = this.doc.getTextWidth(label + ' ');
      this.doc.setFont('helvetica', 'normal');
      const vw = this.doc.getTextWidth(value);
      const totalW = lw + vw + 6;
      if (x + totalW > this.pageWidth - this.marginRight) { x = this.marginLeft; this.currentY += rowH; this.ensure(rowH); }
      this.doc.setFont('helvetica', 'bold'); this.doc.setTextColor(...RC.sub);
      this.doc.text(label, x, this.currentY);
      this.doc.setFont('helvetica', 'normal'); this.doc.setTextColor(...RC.ink);
      this.doc.text(value, x + lw, this.currentY);
      x += totalW;
      if (x < this.pageWidth - this.marginRight - 4) {
        this.doc.setTextColor(...RC.hairline);
        this.doc.text('|', x - 3, this.currentY);
      }
    }
    this.currentY += rowH + 1.5;
    this.doc.setTextColor(...RC.ink);
  }

  _statusStyle(status) {
    switch (status) {
      case 'ok': return { label: 'OK', c: RC.ok, bg: RC.okBg };
      case 'hallu': return { label: 'HALLU', c: RC.hallu, bg: RC.halluBg };
      case 'missing': return { label: 'MISSING', c: RC.missing, bg: RC.missingBg };
      default: return { label: '—', c: RC.sub, bg: RC.cardBg };
    }
  }

  // One fact: status chip + fact text, then optional eval / analysis / chunks.
  factRow(fact) {
    const s = this._statusStyle(fact.status);
    const chipW = 15;
    const textX = this.marginLeft + chipW + 3;
    const textW = this.pageWidth - this.marginRight - textX;

    // chip + first line must fit together
    this._set(9.5, 'normal', RC.ink);
    const lines = this.doc.splitTextToSize(this.sanitize(fact.text), textW);
    const lineH = this._lh(9.5, 1.3);
    this.ensure(Math.max(6, lineH + 2));
    this.currentY += 1.5;

    const chipY = this.currentY - 3;
    this.doc.setFillColor(...s.bg);
    this.doc.roundedRect(this.marginLeft, chipY, chipW, 4.6, 1, 1, 'F');
    this._set(6.8, 'bold', s.c);
    this.doc.text(s.label, this.marginLeft + chipW / 2, chipY + 3.1, { align: 'center' });

    this._set(9.5, 'normal', RC.ink);
    let ty = this.currentY;
    for (let i = 0; i < lines.length; i++) {
      this.ensure(lineH);
      this.doc.text(lines[i], textX, ty === this.currentY ? ty : this.currentY);
      this.currentY += lineH;
    }
    this.currentY += 1;

    // evaluation quote (italic, indented under the fact text)
    if (fact.evaluation) {
      this.addContent(fact.evaluation, { fontSize: 8, fontStyle: 'italic', color: RC.sub, indent: chipW + 3, gapAfter: 1 });
    }

    // problem analysis callout (type in bold + explanation)
    if (fact.problemType && fact.problemExplanation) {
      const indent = chipW + 3;
      const innerW = this.contentWidth - indent - 4;
      this._set(8, 'bold');
      const typeW = this.doc.getTextWidth(fact.problemType + ':  ');
      this._set(8, 'normal');
      const explLines = this.doc.splitTextToSize(this.sanitize(fact.problemExplanation), innerW - typeW);
      const boxH = Math.max(this._lh(8, 1.3), explLines.length * this._lh(8, 1.3)) + 3.5;
      this.ensure(boxH + 2);
      this.doc.setFillColor(...RC.halluBg);
      this.doc.roundedRect(this.marginLeft + indent, this.currentY - 1, innerW + 4, boxH, 1.2, 1.2, 'F');
      let py = this.currentY + 2.6;
      this._set(8, 'bold', RC.hallu);
      this.doc.text(this.sanitize(fact.problemType), this.marginLeft + indent + 3, py);
      this._set(8, 'normal', [120, 40, 45]);
      this.doc.text(explLines[0] || '', this.marginLeft + indent + 3 + typeW, py);
      for (let i = 1; i < explLines.length; i++) {
        py += this._lh(8, 1.3);
        this.doc.text(explLines[i], this.marginLeft + indent + 3, py);
      }
      this.currentY += boxH + 1;
    }

    // chunk evaluation text
    if (fact.chunkEvaluation) {
      this.addContent(fact.chunkEvaluation, { fontSize: 7, color: RC.sub, indent: chipW + 3, gapAfter: 0.5 });
    }

    // retrieved chunks
    if (fact.chunkInfo && fact.chunkInfo.length > 0) {
      for (const chunk of fact.chunkInfo) {
        const indent = chipW + 3;
        const innerW = this.contentWidth - indent - 4;
        this._set(6.5, 'normal', RC.sub);
        const label = `Chunk ${chunk.number}`;
        const cLines = this.doc.splitTextToSize(this.sanitize(chunk.text), innerW - 2);
        const boxH = cLines.length * this._lh(6.5, 1.3) + this._lh(6.5, 1.3) + 3;
        this.ensure(boxH + 1);
        this.doc.setFillColor(...RC.chunkBg);
        this.doc.roundedRect(this.marginLeft + indent, this.currentY - 1, innerW + 4, boxH, 1, 1, 'F');
        let cy = this.currentY + 2.3;
        this._set(6.5, 'bold', RC.brandDark);
        this.doc.text(label, this.marginLeft + indent + 2.5, cy);
        this._set(6.5, 'normal', RC.sub);
        for (const cl of cLines) { cy += this._lh(6.5, 1.3); this.doc.text(cl, this.marginLeft + indent + 2.5, cy); }
        this.currentY += boxH + 1;
      }
    }

    this.currentY += 2.5;
  }

  setStatusColor(doc, status) {
    const s = this._statusStyle(status);
    doc.setFillColor(...s.c);
  }
}

export default {
  name: 'DownloadSimpleReport',
  props: {
    experimentData: {
      type: Object,
      required: true
    },
    meta: {
      type: Object,
      default: () => ({})
    },
    chunkEvalEmpty: {
      type: Boolean,
      default: false
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
        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        const lm = new PDFLayoutManager(doc);

        // ── Cover header ──────────────────────────────────────────────────
        doc.setFillColor(...RC.brand);
        doc.rect(0, 0, lm.pageWidth, 3, 'F');
        lm.currentY = lm.marginTop + 2;
        lm._set(22, 'bold', RC.ink);
        doc.text('Experiment Report', lm.marginLeft, lm.currentY);
        lm.currentY += 7;
        lm._set(9.5, 'normal', RC.sub);
        doc.text(lm.sanitize(this.getExperimentName()), lm.marginLeft, lm.currentY);
        lm.currentY += 4.5;
        doc.text(`Generated ${formatDate(new Date().toISOString())}`, lm.marginLeft, lm.currentY);
        lm.currentY += 3;
        lm.hairline(2, 6);

        // ── Summary ───────────────────────────────────────────────────────
        lm._set(12, 'bold', RC.ink);
        doc.text('Summary', lm.marginLeft, lm.currentY);
        lm.currentY += 2;
        lm.hairline(1, 4, RC.brand);
        lm.addTable({
          head: [['Model', 'Date', 'Facts', 'OK', 'Hallu', 'Missing', 'Extra']],
          body: mainResults.map(result => [
            result.name,
            formatDate(result.date),
            result.facts,
            `${this.calculatePercentage(result.ok, result.facts)}% (${result.ok}/${result.facts})`,
            `${this.calculatePercentage(result.hallu, result.facts)}% (${result.hallu}/${result.facts})`,
            `${this.calculatePercentage(result.missing, result.facts)}% (${result.missing}/${result.facts})`,
            result.extra,
          ]),
        }, {
          theme: 'grid',
          styles: { fontSize: 8, cellPadding: 2.2, textColor: RC.ink, lineColor: RC.cardBorder, lineWidth: 0.1 },
          headStyles: { fillColor: RC.brand, textColor: RC.white, fontStyle: 'bold', fontSize: 8 },
          alternateRowStyles: { fillColor: RC.cardBg },
        });

        // ── Chunk-eval empty state note ───────────────────────────────────
        if (this.chunkEvalEmpty) {
          lm.currentY += 2;
          lm.addContent(
            'Chunk evaluation was enabled, but there was nothing to diagnose — every answer is correct (0 hallucinations, 0 missing facts).',
            { fontSize: 8, fontStyle: 'italic', color: RC.sub, gapAfter: 3 }
          );
        }

        // ── Per-question ──────────────────────────────────────────────────
        for (const result of detailedResults) {
          lm.questionBanner(result.originalIndex, result.question);

          lm.addTable({
            head: [['Facts', 'OK', 'Hallu', 'Missing', 'Extra']],
            body: [[
              result.mainResult.factsCount,
              `${this.calculatePercentage(result.mainResult.ok, result.mainResult.factsCount)}% (${result.mainResult.ok}/${result.mainResult.factsCount})`,
              `${this.calculatePercentage(result.mainResult.hallu, result.mainResult.factsCount)}% (${result.mainResult.hallu}/${result.mainResult.factsCount})`,
              `${this.calculatePercentage(result.mainResult.missing, result.mainResult.factsCount)}% (${result.mainResult.missing}/${result.mainResult.factsCount})`,
              result.mainResult.extra,
            ]],
          }, {
            theme: 'grid',
            styles: { fontSize: 8, cellPadding: 1.8, halign: 'center', textColor: RC.ink, lineColor: RC.cardBorder, lineWidth: 0.1 },
            headStyles: { fillColor: RC.brandFaint, textColor: RC.brandDark, fontStyle: 'bold' },
          });

          // Answer
          lm.subHeader('Answer');
          lm.metaStrip([
            ['Model', result.answerModel],
            ['Date', formatDate(result.answerDate)],
            ['Duration', `${(result.answerDuration || 0).toFixed(2)}s`],
            ['Cost', this.formatCost(result.answerCost)],
          ]);
          lm.addContent(result.answer, { fontSize: 9.5, spacing: 1.4, gapAfter: 3 });

          // Evaluation
          lm.subHeader('Evaluation');
          lm.metaStrip([
            ['Model', result.evalModel],
            ['Date', formatDate(result.evalDate)],
            ['Duration', `${(result.evalDuration || 0).toFixed(2)}s`],
            ['Cost', this.formatCost(result.evalCost)],
          ]);

          // Facts
          lm.subHeader('Facts');
          for (const fact of result.facts) {
            const cleanEval = fact.evaluation ? this.cleanHtml(fact.evaluation) : '';
            lm.factRow({
              status: fact.status,
              text: fact.text,
              evaluation: cleanEval,
              problemType: fact.problemType,
              problemExplanation: fact.problemExplanation,
              chunkEvaluation: fact.chunkEvaluation,
              chunkInfo: fact.chunkInfo,
            });
          }

          lm.hairline(2, 4);
        }

        // ── Footers ───────────────────────────────────────────────────────
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
          doc.setPage(i);
          doc.setDrawColor(...RC.hairline);
          doc.setLineWidth(0.2);
          doc.line(lm.marginLeft, lm.pageHeight - 12, lm.pageWidth - lm.marginRight, lm.pageHeight - 12);
          doc.setFont('helvetica', 'normal');
          doc.setFontSize(7);
          doc.setTextColor(...RC.sub);
          doc.text(`Page ${i} of ${pageCount}`, lm.pageWidth / 2, lm.pageHeight - 8, { align: 'center' });
        }

        doc.save(`${this.getExperimentName()}_report.pdf`);
      } catch (error) {
        console.error('Error generating PDF:', error);
      }
    },

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