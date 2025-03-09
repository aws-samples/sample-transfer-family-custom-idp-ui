<template>
  <div class="row" style="padding-top: .2rem">
    <div class="col-3 field">
      <slot name="label"></slot>
    </div>
    <div class="col-9 input">
      <i class="message">
        <span class="error"><slot name="message"></slot></span>
      </i>
      <slot></slot>
    </div>
  </div>
</template>
<style scoped>
.error {
  color: red;
  font-size: 0.9rem;
  font-weight: normal;
  font-style: italic;
}
</style>
<script setup lang="ts"></script>
