<template>
  <div class="answer-text">
    <textarea v-if="isEditing" v-model="localText" @blur="saveText" class="edit-textarea"></textarea>
    <div v-else v-html="sanitizedText"></div>
  </div>
</template>

<script>
import DOMPurify from 'dompurify';

export default {
  name: 'AnswerText',
  props: {
    text: { type: String, required: true },
    isEditing: { type: Boolean, default: false }
  },
  data() {
    return {
      localText: this.text
    };
  },
  computed: {
    sanitizedText() {
      return DOMPurify.sanitize(this.localText);
    }
  },
  methods: {
    saveText() {
      this.$emit('update', this.localText);
    },
    htmlToPlainText(html) {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;
      return tempDiv.textContent || tempDiv.innerText || '';
    }
  },
  watch: {
    text(newText) {
      this.localText = newText;
    },
    isEditing(newValue) {
      if (newValue) {
        this.localText = this.htmlToPlainText(this.localText);
      } else {
        this.localText = DOMPurify.sanitize(this.localText);
        this.saveText();
      }
    }
  }
};
</script>

<style scoped>
.edit-textarea {
  width: 100%;
  min-height: 200px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
}
</style>