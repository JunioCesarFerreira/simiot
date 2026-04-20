<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { api, type Build } from '../api'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ back: [] }>()

const files = ref<Record<string, string>>({})
const selectedPath = ref<string>('')
const saving = ref(false)
const building = ref(false)
const currentBuild = ref<Build | null>(null)
const builds = ref<Build[]>([])
const error = ref<string | null>(null)
const logsEl = ref<HTMLPreElement | null>(null)
let pollHandle: number | null = null

watch(
  () => currentBuild.value?.logs,
  async () => {
    const el = logsEl.value
    if (!el) return
    // only follow if the user is already near the bottom
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    await nextTick()
    if (nearBottom) el.scrollTop = el.scrollHeight
  },
)

async function loadFirmware() {
  const r = await api.getFirmware(props.projectId)
  files.value = r.files
  const keys = Object.keys(files.value)
  if (!selectedPath.value || !keys.includes(selectedPath.value)) {
    selectedPath.value = keys.includes('main/main.c') ? 'main/main.c' : (keys[0] ?? '')
  }
}

async function loadBuilds() {
  builds.value = await api.listBuilds(props.projectId)
}

async function saveFiles() {
  saving.value = true
  error.value = null
  try {
    await api.putFirmware(props.projectId, files.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

async function runBuild() {
  error.value = null
  try {
    await saveFiles()
    if (error.value) return
    building.value = true
    const b = await api.startBuild(props.projectId)
    currentBuild.value = b
    pollBuild(b.id)
  } catch (e) {
    error.value = (e as Error).message
    building.value = false
  }
}

function pollBuild(buildId: string) {
  stopPoll()
  pollHandle = window.setInterval(async () => {
    try {
      const b = await api.getBuild(props.projectId, buildId)
      currentBuild.value = b
      if (b.status === 'succeeded' || b.status === 'failed') {
        stopPoll()
        building.value = false
        await loadBuilds()
      }
    } catch (e) {
      error.value = (e as Error).message
      stopPoll()
      building.value = false
    }
  }, 1500)
}

function stopPoll() {
  if (pollHandle !== null) {
    clearInterval(pollHandle)
    pollHandle = null
  }
}

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString()
}

onMounted(async () => {
  try {
    await loadFirmware()
    await loadBuilds()
  } catch (e) {
    error.value = (e as Error).message
  }
})

onUnmounted(stopPoll)
</script>

<template>
  <section>
    <button type="button" class="back" @click="emit('back')">← voltar</button>

    <h2>Firmware</h2>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="editor">
      <select v-model="selectedPath">
        <option v-for="(_, path) in files" :key="path" :value="path">{{ path }}</option>
      </select>
      <textarea
        v-if="selectedPath"
        v-model="files[selectedPath]"
        spellcheck="false"
        rows="18"
      />
    </div>

    <div class="actions">
      <button type="button" @click="saveFiles" :disabled="saving || building">
        {{ saving ? 'salvando...' : 'salvar' }}
      </button>
      <button type="button" @click="runBuild" :disabled="building">
        {{ building ? 'compilando...' : 'build' }}
      </button>
    </div>

    <section v-if="currentBuild" class="build-panel">
      <h3>build atual</h3>
      <p>
        status: <strong>{{ currentBuild.status }}</strong>
        <span v-if="currentBuild.exit_code !== null"> (exit {{ currentBuild.exit_code }})</span>
        · iniciado {{ formatTime(currentBuild.started_at) }}
        <span v-if="currentBuild.finished_at"> · finalizado {{ formatTime(currentBuild.finished_at) }}</span>
      </p>
      <pre ref="logsEl" class="logs">{{ currentBuild.logs || '(aguardando logs)' }}</pre>
    </section>

    <section v-if="builds.length" class="history">
      <h3>histórico</h3>
      <ul>
        <li v-for="b in builds" :key="b.id" @click="currentBuild = b">
          <span class="status-pill" :data-status="b.status">{{ b.status }}</span>
          <small>{{ formatTime(b.started_at) }}</small>
        </li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.back { margin-bottom: 1rem; }
.editor { margin: 1rem 0; }
select { padding: 0.4rem; font: inherit; margin-bottom: 0.5rem; }
textarea {
  width: 100%;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 0.85rem;
  padding: 0.75rem;
  box-sizing: border-box;
}
.actions { display: flex; gap: 0.5rem; }
.build-panel, .history { margin-top: 1.5rem; }
.logs {
  background: #0002;
  padding: 1rem;
  border-radius: 6px;
  white-space: pre-wrap;
  max-height: 420px;
  overflow: auto;
  font-size: 0.8rem;
}
.history ul { list-style: none; padding: 0; }
.history li {
  padding: 0.5rem 0.75rem;
  border: 1px solid #8884;
  border-radius: 6px;
  margin-bottom: 0.25rem;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.history li:hover { background: #8881; }
.status-pill { font-size: 0.8rem; font-weight: 600; }
.status-pill[data-status="succeeded"] { color: #2c7; }
.status-pill[data-status="failed"] { color: #c33; }
.status-pill[data-status="running"] { color: #c90; }
.error { color: #c33; }
</style>
