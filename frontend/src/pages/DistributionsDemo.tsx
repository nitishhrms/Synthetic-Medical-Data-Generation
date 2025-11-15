import React from 'react';
import { Tabs } from 'antd';
import { RealVsBootstrap } from './RealVsBootstrap';
import { RealVsMVN } from './RealVsMVN';
import { ThreeWayComparison } from './ThreeWayComparison';
import type { VitalsRecord } from '@/types';

/**
 * Demo page showing all three analytical figures
 * This demonstrates how to wire up the components with real or mocked data
 */

// Helper function to generate mock vitals data
function generateMockData(
  numSubjects: number,
  meanSBP: number,
  stdSBP: number = 10
): VitalsRecord[] {
  const data: VitalsRecord[] = [];
  const visits: Array<'Screening' | 'Day 1' | 'Week 4' | 'Week 12'> = [
    'Screening',
    'Day 1',
    'Week 4',
    'Week 12',
  ];

  for (let i = 0; i < numSubjects; i++) {
    const subjectId = `S${String(i + 1).padStart(3, '0')}`;
    const treatmentArm = i < numSubjects / 2 ? 'Active' : 'Placebo';

    visits.forEach(visit => {
      const sbp = Math.round(
        meanSBP + (Math.random() - 0.5) * 2 * stdSBP + (Math.random() - 0.5) * 10
      );
      const dbp = Math.round(sbp * 0.6 + (Math.random() - 0.5) * 5);
      const hr = Math.round(72 + (Math.random() - 0.5) * 20);
      const temp = Number((36.5 + (Math.random() - 0.5) * 1).toFixed(1));

      data.push({
        SubjectID: subjectId,
        VisitName: visit,
        TreatmentArm: treatmentArm as 'Active' | 'Placebo',
        SystolicBP: sbp,
        DiastolicBP: dbp,
        HeartRate: hr,
        Temperature: temp,
      });
    });
  }

  return data;
}

export const DistributionsDemo: React.FC = () => {
  // Generate mock datasets
  const realData = React.useMemo(() => generateMockData(100, 140, 12), []);
  const mvnData = React.useMemo(() => generateMockData(100, 138, 11), []);
  const bootstrapData = React.useMemo(() => generateMockData(100, 139, 12), []);

  const items = [
    {
      key: 'real-vs-bootstrap',
      label: 'Real vs Bootstrap',
      children: <RealVsBootstrap realData={realData} bootstrapData={bootstrapData} />,
    },
    {
      key: 'real-vs-mvn',
      label: 'Real vs MVN',
      children: <RealVsMVN realData={realData} mvnData={mvnData} />,
    },
    {
      key: 'three-way',
      label: 'Three-Way Comparison',
      children: (
        <ThreeWayComparison
          realData={realData}
          mvnData={mvnData}
          bootstrapData={bootstrapData}
        />
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 'bold', margin: 0 }}>
          Distribution Analysis Dashboard
        </h1>
        <p style={{ color: '#666', marginTop: 8 }}>
          Comprehensive analytical figures for comparing real and synthetic clinical trial data
        </p>
      </div>

      <Tabs defaultActiveKey="real-vs-bootstrap" items={items} size="large" />
    </div>
  );
};
