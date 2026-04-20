<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from './api'
import ProjectList from './components/ProjectList.vue'
import ProjectDetail from './components/ProjectDetail.vue'

const backendStatus = ref<string>('...')
const selectedId = ref<string | null>(null)

onMounted(async () => {
  try {
    const h = await api.health()
    backendStatus.value = h.status
  } catch {
    backendStatus.value = 'offline'
  }
})
</script>

<template>
  <main>
    <header>
      <h1>SimIoT</h1>
      <span class="status" :data-ok="backendStatus === 'ok'">
        backend: {{ backendStatus }}
      </span>
    </header>

    <ProjectDetail
      v-if="selectedId"
      :project-id="selectedId"
      @back="selectedId = null"
    />
    <ProjectList v-else @open="selectedId = $event" />
  </main>
</template>

<style>
:root {
  font-family: system-ui, -apple-system, sans-serif;
  color-scheme: light dark;
}
body { margin: 0; }
main { max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
header { display: flex; align-items: baseline; justify-content: space-between; }
h1 { margin: 0; }
.status { font-size: 0.85rem; opacity: 0.7; }
.status[data-ok="true"] { color: #2c7; }
</style>
