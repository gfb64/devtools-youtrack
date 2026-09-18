const entities = require('@jetbrains/youtrack-scripting-api/entities');

exports.rule = entities.Issue.stateMachine({
  title: 'Standard issue lifecycle',
  fieldName: 'State',
  states: {
    'TO DO': {
      initial: true,
      transitions: {
        start: { targetState: 'IN PROGRESS' },
      },
    },
    'IN PROGRESS': {
      transitions: {
        pause: { targetState: 'TO DO' },
        review: { targetState: 'IN REVIEW' },
      },
    },
    'IN REVIEW': {
      transitions: {
        rework: { targetState: 'TO DO' },
        resume: { targetState: 'IN PROGRESS' },
        done: { targetState: 'DONE' },
      },
    },
    DONE: {
      transitions: {
        reopen: { targetState: 'TO DO' },
      },
    },
  },
});
