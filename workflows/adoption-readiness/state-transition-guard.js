const entities = require('@jetbrains/youtrack-scripting-api/entities');
const workflow = require('@jetbrains/youtrack-scripting-api/workflow');

const allowedTransitions = new Set([
  'TO DO->IN PROGRESS',
  'IN PROGRESS->TO DO',
  'IN PROGRESS->IN REVIEW',
  'IN REVIEW->TO DO',
  'IN REVIEW->IN PROGRESS',
  'IN REVIEW->DONE',
  'DONE->TO DO',
]);

exports.rule = entities.Issue.onChange({
  title: 'Enforce standard state transitions',
  guard: (ctx) => ctx.issue.isReported &&
    !ctx.issue.becomesReported &&
    ctx.issue.fields.isChanged(ctx.State),
  action: (ctx) => {
    const previous = ctx.issue.fields.oldValue(ctx.State);
    const current = ctx.issue.fields.State;
    const transition = `${previous && previous.name}->${current && current.name}`;

    workflow.check(
      allowedTransitions.has(transition),
      `State transition ${transition} is not allowed.`,
    );
  },
  requirements: {
    State: {
      type: entities.State.fieldType,
    },
  },
});
