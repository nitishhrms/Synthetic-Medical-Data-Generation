import React, { useMemo } from 'react';
import { Row, Col, Card, Switch } from 'antd';
import { OverlaidHistogram } from '@/components/Distributions/OverlaidHistogram';
import { BoxPlot } from '@/components/Distributions/BoxPlot';
import { SummaryTable, createNumericColumn, createTextColumn } from '@/components/Cards/SummaryTable';
import ReactECharts from 'echarts-for-react';
import {
  mean,
  std,
  countUnique,
  extractField,
  groupBy,
  calculateDiffPercent,
} from '@/utils/stats';
import type { VitalsRecord } from '@/types';
import type { ColumnsType } from 'antd/es/table';

export interface ThreeWayComparisonProps {
  realData: VitalsRecord[];
  mvnData: VitalsRecord[];
  bootstrapData: VitalsRecord[];
}

/**
 * Figure C: Three-way comparison (12 panels)
 * 1-4: Overlaid density histograms (Real, MVN, Bootstrap) for SBP, DBP, HR, Temperature
 * 5: Records per Visit (three cohorts)
 * 6: Arm Balance (three cohorts)
 * 7-9: Box plots for SBP, DBP, HR (three cohorts each)
 * 10: Comprehensive table with means & counts + diff% columns
 */
export const ThreeWayComparison: React.FC<ThreeWayComparisonProps> = ({
  realData,
  mvnData,
  bootstrapData,
}) => {
  const [useDensity, setUseDensity] = React.useState(true);

  // Extract vital signs data
  const vitalsData = useMemo(() => {
    return {
      SystolicBP: {
        real: extractField(realData, 'SystolicBP'),
        mvn: extractField(mvnData, 'SystolicBP'),
        bootstrap: extractField(bootstrapData, 'SystolicBP'),
      },
      DiastolicBP: {
        real: extractField(realData, 'DiastolicBP'),
        mvn: extractField(mvnData, 'DiastolicBP'),
        bootstrap: extractField(bootstrapData, 'DiastolicBP'),
      },
      HeartRate: {
        real: extractField(realData, 'HeartRate'),
        mvn: extractField(mvnData, 'HeartRate'),
        bootstrap: extractField(bootstrapData, 'HeartRate'),
      },
      Temperature: {
        real: extractField(realData, 'Temperature'),
        mvn: extractField(mvnData, 'Temperature'),
        bootstrap: extractField(bootstrapData, 'Temperature'),
      },
    };
  }, [realData, mvnData, bootstrapData]);

  // Records per Visit
  const recordsPerVisitData = useMemo(() => {
    const realVisits = groupBy(realData, 'VisitName');
    const mvnVisits = groupBy(mvnData, 'VisitName');
    const bootstrapVisits = groupBy(bootstrapData, 'VisitName');
    const visitOrder = ['Screening', 'Day 1', 'Week 4', 'Week 12'];

    return visitOrder.map(visit => ({
      visit,
      Real: realVisits.get(visit)?.length || 0,
      MVN: mvnVisits.get(visit)?.length || 0,
      Bootstrap: bootstrapVisits.get(visit)?.length || 0,
    }));
  }, [realData, mvnData, bootstrapData]);

  // Treatment Arm Balance
  const armBalanceData = useMemo(() => {
    const realArms = groupBy(realData, 'TreatmentArm');
    const mvnArms = groupBy(mvnData, 'TreatmentArm');
    const bootstrapArms = groupBy(bootstrapData, 'TreatmentArm');

    return [
      {
        arm: 'Active',
        Real: countUnique(realArms.get('Active')?.map(r => r.SubjectID) || []),
        MVN: countUnique(mvnArms.get('Active')?.map(r => r.SubjectID) || []),
        Bootstrap: countUnique(bootstrapArms.get('Active')?.map(r => r.SubjectID) || []),
      },
      {
        arm: 'Placebo',
        Real: countUnique(realArms.get('Placebo')?.map(r => r.SubjectID) || []),
        MVN: countUnique(mvnArms.get('Placebo')?.map(r => r.SubjectID) || []),
        Bootstrap: countUnique(bootstrapArms.get('Placebo')?.map(r => r.SubjectID) || []),
      },
    ];
  }, [realData, mvnData, bootstrapData]);

  // Comprehensive Table Data with diff%
  const comprehensiveTableData = useMemo(() => {
    const realSubjects = countUnique(realData.map(r => r.SubjectID));
    const mvnSubjects = countUnique(mvnData.map(r => r.SubjectID));
    const bootstrapSubjects = countUnique(bootstrapData.map(r => r.SubjectID));

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
    const bootstrapActive = countUnique(
      bootstrapData.filter(r => r.TreatmentArm === 'Active').map(r => r.SubjectID)
    );
    const bootstrapPlacebo = countUnique(
      bootstrapData.filter(r => r.TreatmentArm === 'Placebo').map(r => r.SubjectID)
    );

    const meanSBPReal = mean(vitalsData.SystolicBP.real);
    const meanSBPMVN = mean(vitalsData.SystolicBP.mvn);
    const meanSBPBootstrap = mean(vitalsData.SystolicBP.bootstrap);

    const meanDBPReal = mean(vitalsData.DiastolicBP.real);
    const meanDBPMVN = mean(vitalsData.DiastolicBP.mvn);
    const meanDBPBootstrap = mean(vitalsData.DiastolicBP.bootstrap);

    const meanHRReal = mean(vitalsData.HeartRate.real);
    const meanHRMVN = mean(vitalsData.HeartRate.mvn);
    const meanHRBootstrap = mean(vitalsData.HeartRate.bootstrap);

    const meanTempReal = mean(vitalsData.Temperature.real);
    const meanTempMVN = mean(vitalsData.Temperature.mvn);
    const meanTempBootstrap = mean(vitalsData.Temperature.bootstrap);

    return [
      {
        metric: 'Total Records',
        real: realData.length,
        mvn: mvnData.length,
        bootstrap: bootstrapData.length,
        mvnDiff: calculateDiffPercent(mvnData.length, realData.length),
        bootstrapDiff: calculateDiffPercent(bootstrapData.length, realData.length),
      },
      {
        metric: 'Unique Subjects',
        real: realSubjects,
        mvn: mvnSubjects,
        bootstrap: bootstrapSubjects,
        mvnDiff: calculateDiffPercent(mvnSubjects, realSubjects),
        bootstrapDiff: calculateDiffPercent(bootstrapSubjects, realSubjects),
      },
      {
        metric: 'Mean SBP (mmHg)',
        real: meanSBPReal,
        mvn: meanSBPMVN,
        bootstrap: meanSBPBootstrap,
        mvnDiff: calculateDiffPercent(meanSBPMVN, meanSBPReal),
        bootstrapDiff: calculateDiffPercent(meanSBPBootstrap, meanSBPReal),
      },
      {
        metric: 'Mean DBP (mmHg)',
        real: meanDBPReal,
        mvn: meanDBPMVN,
        bootstrap: meanDBPBootstrap,
        mvnDiff: calculateDiffPercent(meanDBPMVN, meanDBPReal),
        bootstrapDiff: calculateDiffPercent(meanDBPBootstrap, meanDBPReal),
      },
      {
        metric: 'Mean HR (bpm)',
        real: meanHRReal,
        mvn: meanHRMVN,
        bootstrap: meanHRBootstrap,
        mvnDiff: calculateDiffPercent(meanHRMVN, meanHRReal),
        bootstrapDiff: calculateDiffPercent(meanHRBootstrap, meanHRReal),
      },
      {
        metric: 'Mean Temp (°C)',
        real: meanTempReal,
        mvn: meanTempMVN,
        bootstrap: meanTempBootstrap,
        mvnDiff: calculateDiffPercent(meanTempMVN, meanTempReal),
        bootstrapDiff: calculateDiffPercent(meanTempBootstrap, meanTempReal),
      },
      {
        metric: 'Active Subjects',
        real: realActive,
        mvn: mvnActive,
        bootstrap: bootstrapActive,
        mvnDiff: calculateDiffPercent(mvnActive, realActive),
        bootstrapDiff: calculateDiffPercent(bootstrapActive, realActive),
      },
      {
        metric: 'Placebo Subjects',
        real: realPlacebo,
        mvn: mvnPlacebo,
        bootstrap: bootstrapPlacebo,
        mvnDiff: calculateDiffPercent(mvnPlacebo, realPlacebo),
        bootstrapDiff: calculateDiffPercent(bootstrapPlacebo, realPlacebo),
      },
    ];
  }, [realData, mvnData, bootstrapData, vitalsData]);

  const comprehensiveColumns: ColumnsType<any> = [
    createTextColumn('Metric', 'metric'),
    createNumericColumn('Real Data', 'real', 1),
    createNumericColumn('MVN', 'mvn', 1),
    createNumericColumn('Bootstrap', 'bootstrap', 1),
    {
      title: 'MVN Diff % vs Real',
      dataIndex: 'mvnDiff',
      key: 'mvnDiff',
      align: 'right',
      render: (value: number) => {
        const formatted = value.toFixed(1);
        const color = Math.abs(value) < 5 ? 'green' : Math.abs(value) < 10 ? 'orange' : 'red';
        return <span style={{ color }}>{formatted}%</span>;
      },
    },
    {
      title: 'Bootstrap Diff % vs Real',
      dataIndex: 'bootstrapDiff',
      key: 'bootstrapDiff',
      align: 'right',
      render: (value: number) => {
        const formatted = value.toFixed(1);
        const color = Math.abs(value) < 5 ? 'green' : Math.abs(value) < 10 ? 'orange' : 'red';
        return <span style={{ color }}>{formatted}%</span>;
      },
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Figure C: Three-Way Comparison (Real vs MVN vs Bootstrap)</h2>
        <div>
          <span style={{ marginRight: 8 }}>Show Counts:</span>
          <Switch checked={!useDensity} onChange={(checked) => setUseDensity(!checked)} />
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {/* Panel 1-4: Vital Signs Distributions (3-way) */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Systolic BP Distribution" size="small">
            <OverlaidHistogram
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.SystolicBP.real, color: '#10b981' },
                { name: 'MVN', data: vitalsData.SystolicBP.mvn, color: '#8b5cf6' },
                { name: 'Bootstrap', data: vitalsData.SystolicBP.bootstrap, color: '#f59e0b' },
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
                { name: 'MVN', data: vitalsData.DiastolicBP.mvn, color: '#8b5cf6' },
                { name: 'Bootstrap', data: vitalsData.DiastolicBP.bootstrap, color: '#f59e0b' },
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
                { name: 'MVN', data: vitalsData.HeartRate.mvn, color: '#8b5cf6' },
                { name: 'Bootstrap', data: vitalsData.HeartRate.bootstrap, color: '#f59e0b' },
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
                { name: 'MVN', data: vitalsData.Temperature.mvn, color: '#8b5cf6' },
                { name: 'Bootstrap', data: vitalsData.Temperature.bootstrap, color: '#f59e0b' },
              ]}
              binCount={30}
              useDensity={useDensity}
              unit="°C"
              height={300}
            />
          </Card>
        </Col>

        {/* Panel 5: Records per Visit (3-way) */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Records per Visit (Three Cohorts)" size="small">
            <ReactECharts
              option={{
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                legend: { data: ['Real Data', 'MVN', 'Bootstrap'] },
                grid: { left: '10%', right: '10%', bottom: '20%', top: '15%', containLabel: true },
                xAxis: {
                  type: 'category',
                  data: recordsPerVisitData.map(d => d.visit),
                  axisLabel: { rotate: 30, fontSize: 10 },
                },
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
                  {
                    name: 'Bootstrap',
                    type: 'bar',
                    data: recordsPerVisitData.map(d => d.Bootstrap),
                    itemStyle: { color: '#f59e0b' },
                  },
                ],
              }}
              style={{ height: 300 }}
            />
          </Card>
        </Col>

        {/* Panel 6: Arm Balance (3-way) */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Treatment Arm Balance (Three Cohorts)" size="small">
            <ReactECharts
              option={{
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                legend: { data: ['Real Data', 'MVN', 'Bootstrap'] },
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
                  {
                    name: 'Bootstrap',
                    type: 'bar',
                    data: armBalanceData.map(d => d.Bootstrap),
                    itemStyle: { color: '#f59e0b' },
                  },
                ],
              }}
              style={{ height: 300 }}
            />
          </Card>
        </Col>

        {/* Panel 7-9: Box Plots for SBP, DBP, HR */}
        <Col xs={24} md={12} lg={12}>
          <Card title="Systolic BP - Box Plot Comparison" size="small">
            <BoxPlot
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.SystolicBP.real, color: '#10b981' },
                { name: 'MVN', data: vitalsData.SystolicBP.mvn, color: '#8b5cf6' },
                { name: 'Bootstrap', data: vitalsData.SystolicBP.bootstrap, color: '#f59e0b' },
              ]}
              categories={['Real Data', 'MVN', 'Bootstrap']}
              unit="mmHg"
              height={300}
            />
          </Card>
        </Col>

        <Col xs={24} md={12} lg={12}>
          <Card title="Diastolic BP - Box Plot Comparison" size="small">
            <BoxPlot
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.DiastolicBP.real, color: '#10b981' },
                { name: 'MVN', data: vitalsData.DiastolicBP.mvn, color: '#8b5cf6' },
                { name: 'Bootstrap', data: vitalsData.DiastolicBP.bootstrap, color: '#f59e0b' },
              ]}
              categories={['Real Data', 'MVN', 'Bootstrap']}
              unit="mmHg"
              height={300}
            />
          </Card>
        </Col>

        <Col xs={24} md={12} lg={12}>
          <Card title="Heart Rate - Box Plot Comparison" size="small">
            <BoxPlot
              title=""
              datasets={[
                { name: 'Real Data', data: vitalsData.HeartRate.real, color: '#10b981' },
                { name: 'MVN', data: vitalsData.HeartRate.mvn, color: '#8b5cf6' },
                { name: 'Bootstrap', data: vitalsData.HeartRate.bootstrap, color: '#f59e0b' },
              ]}
              categories={['Real Data', 'MVN', 'Bootstrap']}
              unit="bpm"
              height={300}
            />
          </Card>
        </Col>

        {/* Panel 10: Comprehensive Table with diff% */}
        <Col xs={24}>
          <Card title="Comprehensive Summary Statistics with Differential Analysis" size="small">
            <SummaryTable
              data={comprehensiveTableData}
              columns={comprehensiveColumns}
              showExport={true}
              fileName="three_way_comparison_summary"
            />
            <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f9ff', borderRadius: 4 }}>
              <p style={{ margin: 0, fontSize: 12, color: '#1e40af' }}>
                <strong>Diff % Interpretation:</strong> Green (&lt;5%) = Excellent match, Orange (5-10%) = Good match,
                Red (&gt;10%) = Significant difference from real data
              </p>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
