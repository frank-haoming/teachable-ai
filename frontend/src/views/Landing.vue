<template>
  <div class="landing">
    <header class="landing-header page-shell">
      <BrandLockup />
      <div class="landing-actions">
        <router-link :to="{ name: 'login' }">
          <el-button plain>登录</el-button>
        </router-link>
        <router-link :to="{ name: 'register' }">
          <el-button type="primary">立即体验</el-button>
        </router-link>
      </div>
    </header>

    <main>
      <!-- Hero -->
      <section class="page-shell hero-layout">
        <div class="hero-copy">
          <span class="eyebrow hero-eyebrow">以教促学 · Learning by Teaching</span>
          <h1 class="hero-title">
            把 AI 当成学生来教，<br />在"教"的过程中真正掌握知识。
          </h1>
          <p class="page-subtitle">
            适用于任何学科——英语、数学、编程、历史……学生教自己的专属 AI，教师通过统一测试与学习分析，
            看见知识如何被组织、纠正、沉淀。
          </p>
          <div class="hero-actions">
            <router-link :to="{ name: 'register' }">
              <el-button type="primary" size="large">免费创建账号</el-button>
            </router-link>
            <router-link :to="{ name: 'login' }">
              <el-button plain size="large">进入已有班级</el-button>
            </router-link>
          </div>
          <div class="hero-metrics">
            <span class="data-chip">📝 对话式知识积累</span>
            <span class="data-chip">🧪 自测不污染记忆</span>
            <span class="data-chip">📊 教师一键测全班</span>
          </div>
        </div>

        <div class="hero-preview glass-card">
          <div class="preview-card preview-card--hero">
            <span class="eyebrow">Teach Flow</span>
            <h3>学生用自然语言教 AI</h3>
            <p class="preview-dialogue">
              <span class="d-student">「牛顿第二定律：F = ma，合外力等于质量乘加速度。」</span>
              <span class="d-ai">「明白了！那如果质量不变，力越大，加速度就越大对吗？你能再举个例子吗？」</span>
            </p>
          </div>
          <div class="preview-grid">
            <div class="preview-card">
              <strong>知识记忆面板</strong>
              <p>规则、例子、修正历史实时可见。</p>
            </div>
            <div class="preview-card">
              <strong>教师分析中心</strong>
              <p>覆盖率、进度、测试成绩一目了然。</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Feature cards -->
      <section class="page-shell soft-grid three-col feature-grid">
        <article class="section-card feature-card">
          <div class="feature-icon" aria-hidden="true">教</div>
          <span class="eyebrow">01 · 教</span>
          <h3>对话式教学，知识自然沉淀</h3>
          <p>学生用自然语言讲解概念、举例子、纠正学习伙伴的错误。它每轮都会追问，帮助学生完善理解。</p>
        </article>
        <article class="section-card feature-card">
          <div class="feature-icon" aria-hidden="true">测</div>
          <span class="eyebrow">02 · 测</span>
          <h3>自测与标准化测试双轨并行</h3>
          <p>学生自由探索不影响长期记忆；教师批量下发题目，比较全班学习伙伴的回答与推理过程。</p>
        </article>
        <article class="section-card feature-card">
          <div class="feature-icon" aria-hidden="true">看</div>
          <span class="eyebrow">03 · 看</span>
          <h3>每一次纠正都留下可见痕迹</h3>
          <p>教师看得到学习伙伴学到了什么、哪里被纠正、哪些知识点仍然薄弱，让教学决策有据可依。</p>
        </article>
      </section>

      <!-- Subject showcase -->
      <section class="page-shell subject-row">
        <span class="eyebrow">可用于任何学科</span>
        <div class="subject-tags">
          <span v-for="subject in subjects" :key="subject" class="subject-tag">{{ subject }}</span>
        </div>
      </section>

      <!-- Trust band -->
      <section class="page-shell trust-band glass-card">
        <div class="trust-band__copy">
          <span class="eyebrow">为何选择以教促学？</span>
          <h2>教别人，是检验自己理解深度的最佳方式。</h2>
          <p>
            "以教促学"（Learning by Teaching）是被大量认知科学研究证实的高效学习策略。
            Apprentice AI 将这一理念落地为可量化、可分析的数字课堂体验。
          </p>
        </div>
        <div class="trust-stats">
          <div class="stat-card">
            <strong>AI 专属记忆</strong>
            <p>每位学生有独立的 AI，教什么记什么</p>
          </div>
          <div class="stat-card">
            <strong>自定义班级</strong>
            <p>教师创建班级，设定知识框架</p>
          </div>
          <div class="stat-card">
            <strong>实时分析</strong>
            <p>覆盖率与修正次数可视化呈现</p>
          </div>
        </div>
      </section>
    </main>

    <footer class="landing-footer page-shell">
      <p class="muted">© 2025 Apprentice AI · 以教促学智能学习平台</p>
    </footer>
  </div>
</template>

<script setup>
import BrandLockup from "@/components/BrandLockup.vue";

const subjects = ["英语语法", "数学推导", "物理定律", "编程概念", "历史事件", "化学方程式", "逻辑推理", "……任何学科"];
</script>

<style scoped>
.landing {
  padding-bottom: 48px;
}

.landing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 28px 0 16px;
}

.landing-actions,
.hero-actions,
.hero-metrics {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Hero */
.hero-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(300px, 0.9fr);
  gap: 36px;
  align-items: center;
  padding-top: 40px;
  padding-bottom: 48px;
}

.hero-eyebrow {
  margin-bottom: 16px;
}

.hero-title {
  margin: 0 0 18px;
  font-family: "Crimson Pro", serif;
  font-size: clamp(2.4rem, 2rem + 1.8vw, 4rem);
  line-height: 1.15;
  letter-spacing: -0.01em;
  color: var(--aa-text);
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-metrics {
  margin-top: 8px;
}

/* Hero preview */
.hero-preview {
  padding: 24px;
  display: grid;
  gap: 16px;
}

.preview-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(13, 148, 136, 0.12);
}

.preview-card--hero {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(209, 250, 229, 0.5) 100%);
}

.preview-dialogue {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.d-student,
.d-ai {
  display: block;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 0.88rem;
  line-height: 1.6;
}

.d-student {
  background: rgba(13, 148, 136, 0.1);
  border-left: 3px solid var(--aa-primary);
  margin-left: auto;
  max-width: 90%;
}

.d-ai {
  background: #fff;
  border: 1px solid rgba(13, 148, 136, 0.12);
  max-width: 90%;
}

.preview-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* Feature cards */
.feature-grid {
  margin-top: 0;
  padding-bottom: 20px;
}

.feature-card {
  padding: 28px 24px;
  transition: box-shadow 200ms ease, transform 200ms ease;
}

.feature-card:hover {
  box-shadow: var(--aa-shadow);
  transform: translateY(-2px);
}

.feature-icon {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(13, 148, 136, 0.08);
  color: var(--aa-primary-deep);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 12px;
  line-height: 1;
}

.feature-card h3 {
  margin: 12px 0 10px;
  font-size: 1.15rem;
  color: var(--aa-text);
}

/* Subject row */
.subject-row {
  padding: 28px 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.subject-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.subject-tag {
  padding: 8px 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--aa-border);
  font-size: 0.92rem;
  color: var(--aa-text);
  box-shadow: var(--aa-shadow-soft);
}

/* Trust band */
.trust-band {
  margin-top: 8px;
  padding: 36px 32px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: start;
}

.trust-band__copy h2 {
  margin: 14px 0 12px;
  font-family: "Crimson Pro", serif;
  font-size: clamp(1.6rem, 1rem + 1.5vw, 2.4rem);
  line-height: 1.2;
}

.trust-band__copy p {
  color: var(--aa-text-soft);
  line-height: 1.75;
}

.trust-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card {
  padding: 16px 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--aa-border);
}

.stat-card strong {
  display: block;
  font-size: 1rem;
  margin-bottom: 4px;
  color: var(--aa-primary-deep);
}

.stat-card p {
  margin: 0;
  color: var(--aa-text-soft);
  font-size: 0.9rem;
}

/* Footer */
.landing-footer {
  padding: 24px 0;
  border-top: 1px solid var(--aa-border);
  margin-top: 40px;
}

@media (max-width: 1024px) {
  .hero-layout,
  .trust-band {
    grid-template-columns: 1fr;
  }

  .preview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .preview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
