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

export interface RealVsBootstrapProps {
  realData: VitalsRecord[];
  bootstrapData: VitalsRecord[];
}

/**
 * Figure A: Real vs Bootstrap (9 panels)
 * 1-4: Overlaid density histograms for SBP, DBP, HR, Temperature
 * 5: Records per Visit (grouped bar)
 * 6: Treatment Arm Balance (grouped bar)
 * 7: Visit Sequence Completeness (stacked bar %)
 * 8: Pulse Pressure distribution
 * 9: Summary table
 */
export const RealVsBootstrap: React.FC<RealVsBootstrapProps> = ({
  realData,
  bootstrapData,
}) => {
  const [useDensity, setUseDensity] = React.useState(true);

  // Extract vital signs data
  const vitalsData = useMemo(() => {
    return {
      SystolicBP: {
        real: extractField(realData, 'SystolicBP'),
        bootstrap: extractField(bootstrapData, 'SystolicBP'),
      },
      DiastolicBP: {
        real: extractField(realData, 'DiastolicBP'),
        bootstrap: extractField(bootstrapData, 'DiastolicBP'),
      },
      HeartRate: {
        real: extractField(realData, 'HeartRate'),
        bootstrap: extractField(bootstrapData, 'HeartRate'),
      },
      Temperature: {
        real: extractField(realData, 'Temperature'),
        bootstrap: extractField(bootstrapData, 'Temperature'),
      },
    };
  }, [realData, bootstrapData]);

  // Calculate pulse pressure (SBP - DBP)
  const pulsePressureData = useMemo(() => {
    const realPP = realData.map(r => r.SystolicBP - r.DiastolicBP);
    const bootstrapPP = bootstrapData.map(r => r.SystolicBP - r.DiastolicBP);
    return { real: realPP, bootstrap: bootstrapPP };
  }, [realData, bootstrapData]);

  // Records per Visit
  const recordsPerVisitData = useMemo(() => {
    const realVisits = groupBy(realData, 'VisitName');
    const bootstrapVisits = groupBy(bootstrapData, 'VisitName');
    const visitOrder = ['Screening', 'Day 1', 'Week 4', 'Week 12'] as const;

    return visitOrder.map(visit => ({
      visit,
      Real: realVisits.get(visit)?.length || 0,
      Bootstrap: bootstrapVisits.get(visit)?.length || 0,
    }));
  }, [realData, bootstrapData]);

  // Treatment Arm Balance
  const armBalanceData = useMemo(() => {
    const realArms = groupBy(realData, 'TreatmentArm');
    const bootstrapArms = groupBy(bootstrapData, 'TreatmentArm');

    return [
      {
        arm: 'Active',
        Real: countUnique(realArms.get('Active')?.map(r => r.SubjectID) || []),
        Bootstrap: countUnique(bootstrapArms.get('Active')?.map(r => r.SubjectID) || []),
      },
      {
        arm: 'Placebo',
        Real: countUnique(realArms.get('Placebo')?.map(r => r.SubjectID) || []),
        Bootstrap: countUnique(bootstrapArms.get('Placebo')?.map(r => r.SubjectID) || []),
      },
    ];
  }, [realData, bootstrapData]);

  // Visit Sequence Completeness
  const visitCompletenessData = useMemo(() => {
    const expectedVisits = ['Screening', 'Day 1', 'Week 4', 'Week 12'];
    const realCompleteness = calculateVisitCompleteness(realData, expectedVisits);
    const bootstrapCompleteness = calculateVisitCompleteness(bootstrapData, expectedVisits);

    const realTotal = realCompleteness.complete + realCompleteness.incomplete;
    const bootstrapTotal = bootstrapCompleteness.complete + bootstrapCompleteness.incomplete;

    return [
      {
        cohort: 'Real Data',
        Complete: realTotal > 0 ? (realCompleteness.complete / realTotal) * 100 : 0,
        Incomplete: realTotal > 0 ? (realCompleteness.incomplete / realTotal) * 100 : 0,
      },
      {
        cohort: 'Bootstrap',
        Complete: bootstrapTotal > 0 ? (bootstrapCompleteness.complete / bootstrapTotal) * 100 : 0,
        Incomplete: bootstrapTotal > 0 ? (bootstrapCompleteness.incomplete / bootstrapTotal) * 100 : 0,
      },
    ];
  }, [realData, bootstrapData]);

  // Summary Table Data
  const summaryTableData = useMemo(() => {
    const realSubjects = countUnique(realData.map(r => r.SubjectID));
    const bootstrapSubjects = countUnique(bootstrapData.map(r => r.SubjectID));

    const realActive = countUnique(
      realData.filter(r => r.TreatmentArm === 'Active').map(r => r.SubjectID)
    );
    const realPlacebo = countUnique(
      realData.filter(r => r.TreatmentArm === 'Placebo').map(r => r.SubjectID)
    );
    const bootstrapActive = countUnique(
      bootstrapData.filter(r => r.TreatmentArm === 'Active').map(r => r.SubjectID)
    );
    const bootstrapPlacebo = countUnique(
      bootstrapData.filter(r => r.TreatmentArm === 'Placebo').map(r => r.SubjectID)
    );

    return [
      {
        metric: 'Total Records',
        real: realData.length,
        bootstrap: bootstrapData.length,
      },
      {
        metric: 'Unique Subjects',
        real: realSubjects,
        bootstrap: bootstrapSubjects,
      },
      {
        metric: 'Mean SBP (mmHg)',
        real: mean(vitalsData.SystolicBP.real),
        bootstrap: mean(vitalsData.SystolicBP.bootstrap),
      },
      {
        metric: 'Mean DBP (mmHg)',
        real: mean(vitalsData.DiastolicBP.real),
        bootstrap: mean(vitalsData.DiastolicBP.bootstrap),
      },
      {
        metric: 'Mean HR (bpm)',
        real: mean(vitalsData.HeartRate.real),
        bootstrap: mean(vitalsData.HeartRate.bootstrap),
      },
      {
        metric: 'Mean Temp (°C)',
        real: mean(vitalsData.Temperature.real),
        bootstrap: mean(vitalsData.Temperature.bootstrap),
      },
      {
        metric: 'Active Subjects',
        real: realActive,
        bootstrap: bootstrapActive,
      },
      {
        metric: 'Placebo Subjects',
        real: realPlacebo,
        bootstrap: bootstrapPlacebo,
      },
    ];
  }, [realData, bootstrapData, vitalsData]);

  const summaryColumns = [
    createTextColumn('Metric', 'metric'),
    createNumericColumn('Real Data', 'real', 1),
    createNumericColumn('Bootstrap', 'bootstrap', 1),
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Figure A: Real vs Bootstrap Comparison</h2>
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
                { name: 'Bootstrap Synthetic', data: vitalsData.SystolicBP.bootstrap, color: '#3b82f6' },
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
                { name: 'Bootstrap Synthetic', data: vitalsData.DiastolicBP.bootstrap, color: '#3b82f6' },
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
                { name: 'Bootstrap Synthetic', data: vitalsData.HeartRate.bootstrap, color: '#3b82f6' },
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
                { name: 'Bootstrap Synthetic', data: vitalsData.Temperature.bootstrap, color: '#3b82f6' },
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
                legend: { data: ['Real Data', 'Bootstrap'] },
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
                    name: 'Bootstrap',
                    type: 'bar',
                    data: recordsPerVisitData.map(d => d.Bootstrap),
                    itemStyle: { color: '#3b82f6' },
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
                legend: { data: ['Real Data', 'Bootstrap'] },
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
                    name: 'Bootstrap',
                    type: 'bar',
                    data: armBalanceData.map(d => d.Bootstrap),
                    itemStyle: { color: '#3b82f6' },
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
                { name: 'Bootstrap Synthetic', data: pulsePressureData.bootstrap, color: '#3b82f6' },
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
              fileName="real_vs_bootstrap_summary"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
