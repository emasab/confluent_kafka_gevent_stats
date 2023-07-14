import http from 'k6/http';

export const options = {
  discardResponseBodies: true,
  scenarios: {
    contacts: {
      executor: 'constant-arrival-rate',

      // Our test should last 10 seconds in total
      duration: '10s',

      // It should start 1000 iterations per `timeUnit`. Note that iterations starting points
      // will be evenly spread across the `timeUnit` period.
      rate: 1000,

      // It should start `rate` iterations per second
      timeUnit: '1s',

      // It should preallocate 20 VUs before starting the test
      preAllocatedVUs: 20,

      // It is allowed to spin up to 100 maximum VUs to sustain the defined
      // constant arrival rate.
      maxVUs: 100,
    },
  },
};

export default function () {
  http.get('http://localhost:8000');
}
