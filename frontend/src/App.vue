<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type Project } from './api'

const projects = ref<Project[]>([])
const backendStatus = ref<string>('...')
const newName = ref('')
const newDescription = ref('')
const error = ref<string | null>(null)

async function refresh() {
  try {
    projects.value = await api.listProjects()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function createProject() {
  if (!newName.value.trim()) return
  try {
    await api.createProject({ name: newName.value, description: newDescription.value })
    newName.value = ''
    newDescription.value = ''
    await refresh()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function removeProject(id: string) {
  try {
    await api.deleteProject(id)
    await refresh()
  } catch (e) {
    error.value = (e as Error).message
  }
}

onMounted(async () => {
  try {
    const h = await api.health()
    backendStatus.value = h.status
  } catch {
    backendStatus.value = 'offline'
  }
  await refresh()
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

    <section>
      <h2>Projetos</h2>

      <form @submit.prevent="createProject">
        <input v-model="newName" placeholder="nome do projeto" required />
        <input v-model="newDescription" placeholder="descrição (opcional)" />
        <button type="submit">criar</button>
      </form>

      <p v-if="error" class="error">{{ error }}</p>

      <ul v-if="projects.length">
        <li v-for="p in projects" :key="p.id">
          <div>
            <strong>{{ p.name }}</strong>
            <small v-if="p.description"> — {{ p.description }}</small>
          </div>
          <button type="button" @click="removeProject(p.id)">remover</button>
        </li>
      </ul>
      <p v-else class="empty">nenhum projeto ainda</p>
    </section>
  </main>
</template>

<style>
:root {
  font-family: system-ui, -apple-system, sans-serif;
  color-scheme: light dark;
}
body { margin: 0; }
main { max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
header { display: flex; align-items: baseline; justify-content: space-between; }
h1 { margin: 0; }
.status { font-size: 0.85rem; opacity: 0.7; }
.status[data-ok="true"] { color: #2c7; }
form { display: flex; gap: 0.5rem; margin: 1rem 0; }
input { flex: 1; padding: 0.5rem; font: inherit; }
button { padding: 0.5rem 1rem; font: inherit; cursor: pointer; }
ul { list-style: none; padding: 0; }
li { display: flex; justify-content: space-between; align-items: center;
     padding: 0.75rem; border: 1px solid #8884; border-radius: 6px; margin-bottom: 0.5rem; }
.empty { opacity: 0.6; font-style: italic; }
.error { color: #c33; }
</style>
