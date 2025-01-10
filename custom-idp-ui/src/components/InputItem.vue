<template>
  <div class="field">
    <i class="message">
      <span class="error"><slot name="message"></slot></span>
    </i>
    <div class="input">
      <slot name="label"></slot>
      <slot></slot>
    </div>
  </div>
</template>
<style scoped>
.error {
  color: red;
  font-size: .9rem;
  font-weight: normal;
  font-style: italic;
}
</style>
<script setup lang="ts">
</script>