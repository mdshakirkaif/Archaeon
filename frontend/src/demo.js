const DEMO_QUESTIONS = [
  "Can you walk me through the billing service you built? What does it do end to end?",
  "I noticed the auth service doesn't use standard JWT. Why was that decision made?",
  "There's a table called 'user_config' with a column 'flag_old'. What's that about?",
  "If someone new touches the payment pipeline, what's the first thing that will break?",
  "Who else on the team understands the deployment process for the worker service?"
]

let questionIndex = 0

export function resetDemoQuestions() {
  questionIndex = 0
  sessionStorage.setItem('archaeon-demo-initialized', 'false')
}

export function demoGetNextQuestion(sessionId) {
  return new Promise(resolve => {
    setTimeout(() => {
      if (questionIndex >= DEMO_QUESTIONS.length) {
        resolve({ done: true })
        return
      }
      const q = DEMO_QUESTIONS[questionIndex]
      questionIndex++
      resolve({ question: q, index: questionIndex, total: DEMO_QUESTIONS.length })
    }, 600)
  })
}

export function demoUploadAnswer(sessionId, audioBlob) {
  return new Promise(resolve => {
    setTimeout(() => resolve({ ok: true }), 800)
  })
}

const TRANSCRIPTIONS = {
  billing: [
    "The billing service handles all payment processing through Stripe.",
    "It was built about two years ago.",
    "There is a retry mechanism with exponential backoff, three retries before failing.",
    "Webhooks handle the callbacks from Stripe for success and failure events.",
    "Edge cases around race conditions were patched last quarter.",
    "The service also generates PDF invoices and stores them in S3."
  ],
  auth: [
    "The auth service uses custom signed tokens instead of standard JWT.",
    "The reason was we needed to embed legacy session IDs during the monolith migration.",
    "JWT would have required a separate database lookup on every request.",
    "So we embedded the session ID directly in the token payload.",
    "It works fine but I would refactor it once the legacy system is fully deprecated.",
    "There is a middleware that validates the token on every protected route."
  ],
  database: [
    "The user_config table with flag_old is a leftover from a migration two years ago.",
    "It was used during the transition from the old user preferences system.",
    "The column is no longer read by any active code path.",
    "We kept it to avoid breaking reports that query it directly.",
    "It should be safe to remove in the next cleanup sprint.",
    "There is a ticket in the backlog for this but nobody has prioritized it."
  ],
  pipeline: [
    "The payment pipeline has a known issue with duplicate webhook events.",
    "Idempotency keys were added but not all services check them properly.",
    "If someone new touches it, they should first understand the webhook retry flow.",
    "Stripe sends events at least once, so duplicate handling is critical.",
    "The pipeline also aggregates data from three different internal services.",
    "Logging is inconsistent across the pipeline stages, which makes debugging hard."
  ],
  deploy: [
    "The worker service deployment runs through GitHub Actions.",
    "It deploys to a Kubernetes cluster using Helm charts.",
    "The initial pipeline was set up a while back and has been stable since.",
    "The rollback procedure is documented in the ops wiki.",
    "There is a staging environment that mirrors production for testing.",
    "Database migrations run automatically as part of the deploy process."
  ],
  default: [
    "Let me think about that for a moment.",
    "From what I remember working on this codebase,",
    "this is an area that has evolved quite a bit over time.",
    "There are some important details worth noting here.",
    "I would recommend checking the architecture docs for the full picture.",
    "That is what I can recall off the top of my head."
  ]
}

function matchTopic(questionText) {
  const lower = questionText.toLowerCase()
  if (lower.includes('billing') || lower.includes('payment') || lower.includes('stripe')) return 'billing'
  if (lower.includes('auth') || lower.includes('jwt') || lower.includes('token') || lower.includes('login')) return 'auth'
  if (lower.includes('table') || lower.includes('flag') || lower.includes('database') || lower.includes('schema') || lower.includes('column')) return 'database'
  if (lower.includes('pipeline') || lower.includes('payment pipeline') || lower.includes('break')) return 'pipeline'
  if (lower.includes('deploy') || lower.includes('worker') || lower.includes('helm') || lower.includes('kubernetes')) return 'deploy'
  return 'default'
}

export function getDemoTranscriptionPhrases(questionText) {
  const topic = matchTopic(questionText)
  return TRANSCRIPTIONS[topic]
}

const CONTEXT_KEY = 'archaeon-demo-context'

export function storeDemoAnswer(question, transcription) {
  const existing = JSON.parse(sessionStorage.getItem(CONTEXT_KEY) || '[]')
  const topic = matchTopic(question)
  existing.push({ question, transcription, topic, timestamp: Date.now() })
  sessionStorage.setItem(CONTEXT_KEY, JSON.stringify(existing))
}

export function getDemoContext() {
  try {
    return JSON.parse(sessionStorage.getItem(CONTEXT_KEY) || '[]')
  } catch {
    return []
  }
}

const DEMO_RESPONSES = [
  {
    keywords: ['auth', 'jwt', 'token', 'login', 'sign in', 'authentication'],
    answer: 'The auth service uses custom signed tokens because legacy session IDs needed to be embedded during the monolith migration. Standard JWT would have required a database lookup on every request to map the token back to the session.'
  },
  {
    keywords: ['billing', 'payment', 'stripe', 'invoice', 'paid', 'charge'],
    answer: 'The billing service handles payment processing through Stripe with a retry mechanism for failed payments — three retries with exponential backoff. It generates invoices and handles webhook events from Stripe.'
  },
  {
    keywords: ['deploy', 'deployment', 'ci', 'cd', 'pipeline', 'worker', 'helm', 'kubernetes'],
    answer: 'Deployment runs through GitHub Actions. The worker service deploys to a Kubernetes cluster using Helm charts. Rollback procedure is in the ops wiki.'
  },
  {
    keywords: ['database', 'db', 'postgres', 'table', 'schema', 'flag_old', 'migration', 'column'],
    answer: 'PostgreSQL with a shared database for most services. The user_config table with flag_old is leftover from a migration — it can be deprecated but nobody has gotten around to it.'
  },
  {
    keywords: ['who', 'owner', 'responsible', 'talk', 'contact', 'team'],
    answer: 'The billing service has one primary owner. The API layer and Slack integration have another. Infrastructure and pipelines are handled by a third person. Check the team spreadsheet for current assignments.'
  }
]

export function demoAskQuestion(text) {
  return new Promise(resolve => {
    setTimeout(() => {
      const lower = text.toLowerCase()
      const match = DEMO_RESPONSES.find(r => r.keywords.some(k => lower.includes(k)))
      if (match) {
        resolve({ answer: match.answer, citations: [] })
      } else {
        resolve({
          answer: 'Could not find a direct match. The demo covers a few topics: auth, billing, deployment, and database. Try asking about one of those.',
          citations: []
        })
      }
    }, 1200)
  })
}
