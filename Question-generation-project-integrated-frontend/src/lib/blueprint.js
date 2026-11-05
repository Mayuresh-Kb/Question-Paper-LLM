export function buildPayload(uploadId, draft, units) {
  const plans = units.filter(u => draft.plans[u.id]?.selected).map(u => ({
    unit_id: u.id,
    marks: Number(draft.plans[u.id].marks),
    questions_per_alternative: Number(draft.plans[u.id].count),
  }));
  if (!uploadId || !plans.length) throw new Error('Select at least one uploaded unit.');
  if (draft.paper_format === 'unit_test') {
    if (plans.length !== 2) throw new Error('A 16-mark unit test must contain exactly two units.');
    if (plans.some(plan => plan.marks !== 8)) throw new Error('A 16-mark unit test assigns 8 marks to each unit.');
  }
  for (const plan of plans) {
    if (!Number.isInteger(plan.marks) || plan.marks < 1 || plan.marks > 200) throw new Error('Unit marks must be a whole number between 1 and 200.');
    if (!Number.isInteger(plan.questions_per_alternative) || plan.questions_per_alternative < 1 || plan.questions_per_alternative > 12) throw new Error('Choose between 1 and 12 subquestions per alternative.');
    if (plan.marks < plan.questions_per_alternative) throw new Error('Each subquestion needs at least one mark.');
    const unit = units.find(u => u.id === plan.unit_id);
    const available = unit.questions.filter(q => q.enabled).length;
    if (available < 2*plan.questions_per_alternative) throw new Error(`${unit.name} needs ${2*plan.questions_per_alternative} enabled questions for two alternatives; it has ${available}.`);
  }
  return { upload_id: uploadId, header: draft.header, mode: draft.mode, difficulty: draft.difficulty,
    paper_format: draft.paper_format || 'custom',
    total_marks: plans.reduce((sum, p) => sum + p.marks, 0), units: plans };
}
export function initialDraft(units) {
  return { paper_format: 'unit_test', mode: 'balanced', difficulty: 'balanced', header: {
    institution: "Marathwada Mitra Mandal's College of Engineering, Pune",
    exam_name: 'Unit Test', subject: '', duration: '1 hour',
    date: new Date().toLocaleDateString('en-CA'),
    instructions: 'Figures to the right indicate marks.\nAssume suitable data where necessary.',
  }, plans: Object.fromEntries(units.map((u,index) => [u.id, { selected: index < 2, marks: 8, count: 2 }])) };
}
