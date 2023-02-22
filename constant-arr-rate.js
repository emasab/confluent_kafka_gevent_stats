import http from 'k6/http';

export const options = {
  discardResponseBodies: true,
  scenarios: {
    contacts: {
      executor: 'constant-arrival-rate',

      // Our test should last 30 seconds in total
      duration: '30s',

      // It should start 100 iterations per `timeUnit`. Note that iterations starting points
      // will be evenly spread across the `timeUnit` period.
      rate: 100,

      // It should start `rate` iterations per second
      timeUnit: '1s',

      // It should preallocate 20 VUs before starting the test
      preAllocatedVUs: 20,

      // It is allowed to spin up to 20 maximum VUs to sustain the defined
      // constant arrival rate.
      maxVUs: 20,
    },
  },
};

export default function () {
  http.get('http://localhost:8000');
}
