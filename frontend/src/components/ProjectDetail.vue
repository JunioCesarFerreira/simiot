<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { api, type Build, type Run } from '../api'

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ back: [] }>()

const files = ref<Record<string, string>>({})
const selectedPath = ref<string>('')
const saving = ref(false)
const building = ref(false)
const currentBuild = ref<Build | null>(null)
const builds = ref<Build[]>([])
const run = ref<Run | null>(null)
const error = ref<string | null>(null)
const logsEl = ref<HTMLPreElement | null>(null)
const runLogsEl = ref<HTMLPreElement | null>(null)
let buildPoll: number | null = null
let runPoll: number | null = null

const canStartRun = computed(
  () =>
    builds.value.some((b) => b.status === 'succeeded') &&
    (!run.value || ['idle', 'stopped', 'failed'].includes(run.value.status)),
)
const canStopRun = computed(
  () => run.value?.status === 'running',
)

function stickyFollow(el: HTMLPreElement | null) {
  if (!el) return
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
  nextTick(() => {
    if (nearBottom) el.scrollTop = el.scrollHeight
  })
}

watch(() => currentBuild.value?.logs, () => stickyFollow(logsEl.value))
watch(() => run.value?.logs, () => stickyFollow(runLogsEl.value))

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

async function loadRun() {
  run.value = await api.getRun(props.projectId)
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
  stopBuildPoll()
  buildPoll = window.setInterval(async () => {
    try {
      const b = await api.getBuild(props.projectId, buildId)
      currentBuild.value = b
      if (b.status === 'succeeded' || b.status === 'failed') {
        stopBuildPoll()
        building.value = false
        await loadBuilds()
      }
    } catch (e) {
      error.value = (e as Error).message
      stopBuildPoll()
      building.value = false
    }
  }, 1500)
}

async function startExecution() {
  error.value = null
  try {
    run.value = await api.startRun(props.projectId)
    pollRun()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function stopExecution() {
  error.value = null
  try {
    run.value = await api.stopRun(props.projectId)
  } catch (e) {
    error.value = (e as Error).message
  }
}

function pollRun() {
  stopRunPoll()
  runPoll = window.setInterval(async () => {
    try {
      const r = await api.getRun(props.projectId)
      run.value = r
      if (r.status === 'stopped' || r.status === 'failed' || r.status === 'idle') {
        stopRunPoll()
      }
    } catch (e) {
      error.value = (e as Error).message
      stopRunPoll()
    }
  }, 2000)
}

function stopBuildPoll() {
  if (buildPoll !== null) {
    clearInterval(buildPoll)
    buildPoll = null
  }
}

function stopRunPoll() {
  if (runPoll !== null) {
    clearInterval(runPoll)
    runPoll = null
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
    await loadRun()
    if (run.value && (run.value.status === 'running' || run.value.status === 'stopping')) {
      pollRun()
    }
  } catch (e) {
    error.value = (e as Error).message
  }
})

onUnmounted(() => {
  stopBuildPoll()
  stopRunPoll()
})
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

    <section v-if="currentBuild" class="panel">
      <h3>build atual</h3>
      <p>
        status: <span class="status-pill" :data-status="currentBuild.status">{{ currentBuild.status }}</span>
        <span v-if="currentBuild.exit_code !== null"> (exit {{ currentBuild.exit_code }})</span>
        · iniciado {{ formatTime(currentBuild.started_at) }}
        <span v-if="currentBuild.finished_at"> · finalizado {{ formatTime(currentBuild.finished_at) }}</span>
      </p>
      <pre ref="logsEl" class="logs">{{ currentBuild.logs || '(aguardando logs)' }}</pre>
    </section>

    <section v-if="builds.length" class="panel">
      <h3>histórico de builds</h3>
      <ul class="history">
        <li v-for="b in builds" :key="b.id" @click="currentBuild = b">
          <span class="status-pill" :data-status="b.status">{{ b.status }}</span>
          <small>{{ formatTime(b.started_at) }}</small>
        </li>
      </ul>
    </section>

    <section class="panel">
      <h3>execução (QEMU)</h3>
      <p>
        status:
        <span class="status-pill" :data-status="run?.status ?? 'idle'">{{ run?.status ?? 'idle' }}</span>
        <span v-if="run?.started_at"> · iniciado {{ formatTime(run.started_at) }}</span>
        <span v-if="run?.finished_at"> · finalizado {{ formatTime(run.finished_at) }}</span>
      </p>
      <div class="actions">
        <button type="button" @click="startExecution" :disabled="!canStartRun">
          executar
        </button>
        <button type="button" @click="stopExecution" :disabled="!canStopRun">
          parar
        </button>
      </div>
      <p v-if="!builds.some((b) => b.status === 'succeeded')" class="hint">
        é preciso ter um build bem-sucedido antes de executar.
      </p>
      <pre ref="runLogsEl" class="logs">{{ run?.logs || '(sem saída ainda)' }}</pre>
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
.actions { display: flex; gap: 0.5rem; margin: 0.5rem 0; }
.panel { margin-top: 1.5rem; }
.logs {
  background: #0002;
  padding: 1rem;
  border-radius: 6px;
  white-space: pre-wrap;
  max-height: 420px;
  overflow: auto;
  font-size: 0.8rem;
}
.history { list-style: none; padding: 0; }
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
.status-pill { font-size: 0.8rem; font-weight: 600; text-transform: lowercase; }
.status-pill[data-status="succeeded"],
.status-pill[data-status="running"] { color: #2c7; }
.status-pill[data-status="failed"] { color: #c33; }
.status-pill[data-status="pending"],
.status-pill[data-status="stopping"] { color: #c90; }
.status-pill[data-status="stopped"],
.status-pill[data-status="idle"] { color: #888; }
.hint { opacity: 0.7; font-style: italic; font-size: 0.85rem; }
.error { color: #c33; }
</style>
