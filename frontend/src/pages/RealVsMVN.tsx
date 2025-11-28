import React, { useMemo } from 'react';
import { Row, Col, Card, Switch } from 'antd';
import { OverlaidHistogram } from '@/components/Distributions/OverlaidHistogram';
import { SummaryTable, createNumericColumn, createTextColumn } from '@/components/Cards/SummaryTable';
import ReactECharts from 'echarts-for-react';
import {
  mean,
  countUnique,
  extractField,
  groupBy,
  calculateVisitCompleteness,
} from '@/utils/stats';
import type { VitalsRecord } from '@/types';

export interface RealVsMVNProps {
  realData: VitalsRecord[];
  mvnData: VitalsRecord[];
}

/**
 * Figure B: Real vs MVN (9 panels)
 * Same structure as Figure A but comparing Real vs MVN synthetic data
 */
export const RealVsMVN: React.FC<RealVsMVNProps> = ({
  realData,
  mvnData,
}) => {
  const [useDensity, setUseDensity] = React.useState(true);

  // Extract vital signs data
  const vitalsData = useMemo(() => {
    return {
      SystolicBP: {
        real: extractField(realData, 'SystolicBP'),
        mvn: extractField(mvnData, 'SystolicBP'),
      },
      DiastolicBP: {
        real: extractField(realData, 'DiastolicBP'),
        mvn: extractField(mvnData, 'DiastolicBP'),
      },
      HeartRate: {
        real: extractField(realData, 'HeartRate'),
        mvn: extractField(mvnData, 'HeartRate'),
      },
      Temperature: {
        real: extractField(realData, 'Temperature'),
        mvn: extractField(mvnData, 'Temperature'),
      },
    };
  }, [realData, mvnData]);

  // Calculate pulse pressure (SBP - DBP)
  const pulsePressureData = useMemo(() => {
    const realPP = realData.map(r => r.SystolicBP - r.DiastolicBP);
    const mvnPP = mvnData.map(r => r.SystolicBP - r.DiastolicBP);
    return { real: realPP, mvn: mvnPP };
  }, [realData, mvnData]);

  // Records per Visit
  const recordsPerVisitData = useMemo(() => {
    const realVisits = groupBy(realData, 'VisitName');
    const mvnVisits = groupBy(mvnData, 'VisitName');
    const visitOrder = ['Screening', 'Day 1', 'Week 4', 'Week 12'] as const;

    return visitOrder.map(visit => ({
      visit,
      Real: realVisits.get(visit)?.length || 0,
      MVN: mvnVisits.get(visit)?.length || 0,
    }));
  }, [realData, mvnData]);

  // Treatment Arm Balance
  const armBalanceData = useMemo(() => {
    const realArms = groupBy(realData, 'TreatmentArm');
    const mvnArms = groupBy(mvnData, 'TreatmentArm');

    return [
      {
        arm: 'Active',
        Real: countUnique(realArms.get('Active')?.map(r => r.SubjectID) || []),
        MVN: countUnique(mvnArms.get('Active')?.map(r => r.SubjectID) || []),
      },
      {
        arm: 'Placebo',
        Real: countUnique(realArms.get('Placebo')?.map(r => r.SubjectID) || []),
        MVN: countUnique(mvnArms.get('Placebo')?.map(r => r.SubjectID) || []),
      },
    ];
  }, [realData, mvnData]);

  // Visit Sequence Completeness
  const visitCompletenessData = useMemo(() => {
    const expectedVisits = ['Screening', 'Day 1', 'Week 4', 'Week 12'];
    const realCompleteness = calculateVisitCompleteness(realData, expectedVisits);
    const mvnCompleteness = calculateVisitCompleteness(mvnData, expectedVisits);

    const realTotal = realCompleteness.complete + realCompleteness.incomplete;
    const mvnTotal = mvnCompleteness.complete + mvnCompleteness.incomplete;

    return [
      {
        cohort: 'Real Data',
        Complete: realTotal > 0 ? (realCompleteness.complete / realTotal) * 100 : 0,
        Incomplete: realTotal > 0 ? (realCompleteness.incomplete / realTotal) * 100 : 0,
      },
      {
        cohort: 'MVN',
        Complete: mvnTotal > 0 ? (mvnCompleteness.complete / mvnTotal) * 100 : 0,
        Incomplete: mvnTotal > 0 ? (mvnCompleteness.incomplete / mvnTotal) * 100 : 0,
      },
    ];
  }, [realData, mvnData]);

  // Summary Table Data
  const summaryTableData = useMemo(() => {
    const realSubjects = countUnique(realData.map(r => r.SubjectID));
    const mvnSubjects = countUnique(mvnData.map(r => r.SubjectID));

    const realActive = countUnique(
      realData.filter(r => r.TreatmentArm === 'Active').map(r => r.SubjectID)
    );
    const realPlacebo = countUnique(
      realData.filter(r => r.TreatmentArm === 'Placebo').map(r => r.SubjectID)
    );
    const mvnActive = countUnique(
      mvnData.filter(r => r.TreatmentArm === 'Active').map(r => r.SubjectID)
    );
    const mvnPlacebo = countUnique(
      mvnData.filter(r => r.TreatmentArm === 'Placebo').map(r => r.SubjectID)
    );

    return [
      {
        metric: 'Total Records',
        real: realData.length,
        mvn: mvnData.length,
      },
      {
        metric: 'Unique Subjects',
        real: realSubjects,
        mvn: mvnSubjects,
      },
      {
        metric: 'Mean SBP (mmHg)',
        real: mean(vitalsData.SystolicBP.real),
        mvn: mean(vitalsData.SystolicBP.mvn),
      },
      {
        metric: 'Mean DBP (mmHg)',
        real: mean(vitalsData.DiastolicBP.real),
        mvn: mean(vitalsData.DiastolicBP.mvn),
      },
      {
        metric: 'Mean HR (bpm)',
        real: mean(vitalsData.HeartRate.real),
        mvn: mean(vitalsData.HeartRate.mvn),
      },
      {
        metric: 'Mean Temp (°C)',
        real: mean(vitalsData.Temperature.real),
        mvn: mean(vitalsData.Temperature.mvn),
      },
      {
        metric: 'Active Subjects',
        real: realActive,
        mvn: mvnActive,
      },
      {
        metric: 'Placebo Subjects',
        real: realPlacebo,
        mvn: mvnPlacebo,
      },
    ];
  }, [realData, mvnData, vitalsData]);

  const summaryColumns = [
    createTextColumn('Metric', 'metric'),
    createNumericColumn('Real Data', 'real', 1),
    createNumericColumn('MVN', 'mvn', 1),
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Figure B: Real vs MVN Comparison</h2>
        <div>
          <span style={{ marginRight: 8 }}>Show Counts:</span>
          <Switch checked={!useDensity} onChange={(checked) => setUseDensity(!checked)} />
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {/* Panel 1-4: Vital Signs Distributions */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Systolic BP Distribution" size="small">
            <OverlaidHistogram
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.SystolicBP.real, color: '#10b981' },
                { name: 'MVN Synthetic', data: vitalsData.SystolicBP.mvn, color: '#8b5cf6' },
              ]}
              binCount={30}
              useDensity={useDensity}
              unit="mmHg"
              height={300}
            />
          </Card>
        </Col>

        <Col xs={24} md={12} lg={12}>
          <Card title="Diastolic BP Distribution" size="small">
            <OverlaidHistogram
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.DiastolicBP.real, color: '#10b981' },
                { name: 'MVN Synthetic', data: vitalsData.DiastolicBP.mvn, color: '#8b5cf6' },
              ]}
              binCount={30}
              useDensity={useDensity}
              unit="mmHg"
              height={300}
            />
          </Card>
        </Col>

        <Col xs={24} md={12} lg={12}>
          <Card title="Heart Rate Distribution" size="small">
            <OverlaidHistogram
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.HeartRate.real, color: '#10b981' },
                { name: 'MVN Synthetic', data: vitalsData.HeartRate.mvn, color: '#8b5cf6' },
              ]}
              binCount={30}
              useDensity={useDensity}
              unit="bpm"
              height={300}
            />
          </Card>
        </Col>

        <Col xs={24} md={12} lg={12}>
          <Card title="Temperature Distribution" size="small">
            <OverlaidHistogram
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.Temperature.real, color: '#10b981' },
                { name: 'MVN Synthetic', data: vitalsData.Temperature.mvn, color: '#8b5cf6' },
              ]}
              binCount={30}
              useDensity={useDensity}
              unit="°C"
              height={300}
            />
          </Card>
        </Col>

        {/* Panel 5: Records per Visit */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Records per Visit" size="small">
            <ReactECharts
              option={{
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                legend: { data: ['Real Data', 'MVN'] },
                grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
                xAxis: { type: 'category', data: recordsPerVisitData.map(d => d.visit) },
                yAxis: { type: 'value', name: 'Record Count' },
                series: [
                  {
                    name: 'Real Data',
                    type: 'bar',
                    data: recordsPerVisitData.map(d => d.Real),
                    itemStyle: { color: '#10b981' },
                  },
                  {
                    name: 'MVN',
                    type: 'bar',
                    data: recordsPerVisitData.map(d => d.MVN),
                    itemStyle: { color: '#8b5cf6' },
                  },
                ],
              }}
              style={{ height: 300 }}
            />
          </Card>
        </Col>

        {/* Panel 6: Treatment Arm Balance */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Treatment Arm Balance" size="small">
            <ReactECharts
              option={{
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                legend: { data: ['Real Data', 'MVN'] },
                grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
                xAxis: { type: 'category', data: armBalanceData.map(d => d.arm) },
                yAxis: { type: 'value', name: 'Subject Count' },
                series: [
                  {
                    name: 'Real Data',
                    type: 'bar',
                    data: armBalanceData.map(d => d.Real),
                    itemStyle: { color: '#10b981' },
                  },
                  {
                    name: 'MVN',
                    type: 'bar',
                    data: armBalanceData.map(d => d.MVN),
                    itemStyle: { color: '#8b5cf6' },
                  },
                ],
              }}
              style={{ height: 300 }}
            />
          </Card>
        </Col>

        {/* Panel 7: Visit Sequence Completeness */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Visit Sequence Completeness (%)" size="small">
            <ReactECharts
              option={{
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                legend: { data: ['Complete', 'Incomplete'] },
                grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
                xAxis: { type: 'category', data: visitCompletenessData.map(d => d.cohort) },
                yAxis: { type: 'value', name: 'Percentage (%)', max: 100 },
                series: [
                  {
                    name: 'Complete',
                    type: 'bar',
                    stack: 'total',
                    data: visitCompletenessData.map(d => d.Complete.toFixed(1)),
                    itemStyle: { color: '#10b981' },
                    label: { show: true, formatter: '{c}%' },
                  },
                  {
                    name: 'Incomplete',
                    type: 'bar',
                    stack: 'total',
                    data: visitCompletenessData.map(d => d.Incomplete.toFixed(1)),
                    itemStyle: { color: '#ef4444' },
                    label: { show: true, formatter: '{c}%' },
                  },
                ],
              }}
              style={{ height: 300 }}
            />
          </Card>
        </Col>

        {/* Panel 8: Pulse Pressure */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Pulse Pressure Distribution (SBP - DBP)" size="small">
            <OverlaidHistogram
              title=""
              datasets={[
                { name: 'Real Data', data: pulsePressureData.real, color: '#10b981' },
                { name: 'MVN Synthetic', data: pulsePressureData.mvn, color: '#8b5cf6' },
              ]}
              binCount={30}
              useDensity={useDensity}
              unit="mmHg"
              height={300}
            />
          </Card>
        </Col>

        {/* Panel 9: Summary Table */}
        <Col xs={24}>
          <Card title="Summary Statistics" size="small">
            <SummaryTable
              data={summaryTableData}
              columns={summaryColumns}
              showExport={true}
              fileName="real_vs_mvn_summary"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
