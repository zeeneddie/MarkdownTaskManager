/**
 * Test Data for Constitution Command
 *
 * Sample business cases for testing
 */

import { ConstitutionInput } from '../../types/SpecKit';

/**
 * Sample business case: Customer Portal
 */
export const SAMPLE_BUSINESS_CASE_1: ConstitutionInput = {
  businessCase: `
Build a customer self-service portal to reduce support tickets by 50%.
Customers must be able to view their account information, submit support requests,
track ticket status, and access knowledge base articles.
The system should integrate with our existing CRM and ticketing system.
`,
  stakeholders: ['customers', 'support team', 'management'],
  constraints: [
    'Must integrate with existing Salesforce CRM',
    'GDPR compliance is mandatory',
    'Budget constraint: €50,000',
    'Must launch within 3 months'
  ],
  successCriteria: [
    '50% reduction in support tickets within 6 months',
    '90% customer satisfaction score',
    'Average response time < 1 second',
    '99.9% uptime'
  ],
  technicalContext: {
    existingSystems: ['Salesforce CRM', 'Zendesk'],
    technologies: ['React', 'Node.js', 'PostgreSQL'],
    teamSize: 5,
    timeline: '3 months'
  }
};

/**
 * Sample business case: E-commerce Platform
 */
export const SAMPLE_BUSINESS_CASE_2: ConstitutionInput = {
  businessCase: `
Create a modern e-commerce platform to sell products online.
Users should be able to browse products, add to cart, checkout, and track orders.
The platform must support multiple payment methods and provide real-time inventory management.
`,
  stakeholders: ['online shoppers', 'store managers', 'administrators'],
  constraints: [
    'PCI-DSS compliance for payment processing',
    'Must support mobile devices',
    'Performance: page load < 2 seconds'
  ],
  successCriteria: [
    '1000+ orders per day',
    'Conversion rate > 3%',
    'Cart abandonment < 70%'
  ]
};

/**
 * Sample business case: Internal Tool
 */
export const SAMPLE_BUSINESS_CASE_3: ConstitutionInput = {
  businessCase: `
Develop an internal employee management system for HR department.
System must allow creating employee records, managing time off requests,
tracking performance reviews, and generating reports.
`,
  stakeholders: ['HR team', 'employees', 'managers'],
  constraints: [
    'Must integrate with Active Directory',
    'Data privacy regulations',
    'Limited to 100 employees initially'
  ],
  successCriteria: [
    'Reduce HR admin time by 30%',
    'Employee self-service adoption > 80%'
  ]
};
