const entities = require('@jetbrains/youtrack-scripting-api/entities');

exports.rule = entities.Issue.onChange({
  title: 'Reset readiness when a done issue is reopened',
  guard: (ctx) => ctx.issue.isReported &&
    !ctx.issue.becomesReported &&
    ctx.issue.fields.was(ctx.State, ctx.State.Done) &&
    ctx.issue.fields.becomes(ctx.State, ctx.State.ToDo),
  action: (ctx) => {
    ctx.issue.fields.AgentReadiness = ctx.AgentReadiness.PendingReview;
  },
  requirements: {
    State: {
      type: entities.State.fieldType,
      ToDo: { name: 'TO DO' },
      Done: { name: 'DONE' },
    },
    AgentReadiness: {
      type: entities.EnumField.fieldType,
      name: 'Agent Readiness',
      PendingReview: { name: 'Pending Review' },
    },
  },
});
