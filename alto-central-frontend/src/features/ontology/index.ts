/**
 * Ontology feature - Mock implementation for standalone frontend
 */

// Types
export interface OntologyTag {
  [key: string]: string | boolean | number;
}

export interface DataPoint {
  value: any;
  updated_at: string;
  definition: string | null;
  enum: Record<string, string>;
  is_stale: boolean;
}

export interface OntologyEntity {
  entity_id: string;
  name: string;
  tags: OntologyTag;
  latest_data?: Record<string, DataPoint>;
  created_at: string;
  updated_at: string;
}

export interface OntologyQueryParams {
  tags?: string | string[];
  any_tags?: string | string[];
  tag_filter?: string | Record<string, string>;
  expand?: string | string[];
  ref_filter?: string;
  datapoints?: string | string[];
  exclude_stale?: boolean;
  page_size?: number;
  page?: number;
}

export interface UseOntologyEntitiesResult {
  entities: OntologyEntity[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

// Mock equipment data
const mockEntities: OntologyEntity[] = [
  // Chillers
  { entity_id: 'ch-1', name: 'Chiller 1', tags: { model: 'chiller', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ch-2', name: 'Chiller 2', tags: { model: 'chiller', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ch-3', name: 'Chiller 3', tags: { model: 'chiller', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ch-4', name: 'Chiller 4', tags: { model: 'chiller', spaceRef: 'plant' }, latest_data: { status_read: { value: 1, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },

  // Primary Chilled Water Pumps
  { entity_id: 'pchp-1', name: 'PCHP 1', tags: { model: 'pchp', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'pchp-2', name: 'PCHP 2', tags: { model: 'pchp', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'pchp-3', name: 'PCHP 3', tags: { model: 'pchp', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'pchp-4', name: 'PCHP 4', tags: { model: 'pchp', spaceRef: 'plant' }, latest_data: { status_read: { value: 1, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },

  // Condenser Water Pumps
  { entity_id: 'cdp-1', name: 'CDP 1', tags: { model: 'cdp', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'cdp-2', name: 'CDP 2', tags: { model: 'cdp', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'cdp-3', name: 'CDP 3', tags: { model: 'cdp', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'cdp-4', name: 'CDP 4', tags: { model: 'cdp', spaceRef: 'plant' }, latest_data: { status_read: { value: 1, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },

  // Cooling Towers
  { entity_id: 'ct-1', name: 'CT 1', tags: { model: 'ct', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ct-2', name: 'CT 2', tags: { model: 'ct', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ct-3', name: 'CT 3', tags: { model: 'ct', spaceRef: 'plant' }, latest_data: { status_read: { value: 1, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ct-4', name: 'CT 4', tags: { model: 'ct', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ct-5', name: 'CT 5', tags: { model: 'ct', spaceRef: 'plant' }, latest_data: { status_read: { value: 1, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
  { entity_id: 'ct-6', name: 'CT 6', tags: { model: 'ct', spaceRef: 'plant' }, latest_data: { status_read: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false }, alarm: { value: 0, updated_at: '', definition: null, enum: {}, is_stale: false } }, created_at: '', updated_at: '' },
];

// Hook implementation
export function useOntologyEntities(_params: OntologyQueryParams): UseOntologyEntitiesResult {
  return {
    entities: mockEntities,
    loading: false,
    error: null,
    refetch: async () => {},
  };
}

export function useOntologyEntitiesRealtime(params: OntologyQueryParams, _pollingInterval?: number): UseOntologyEntitiesResult {
  return useOntologyEntities(params);
}

export function useOntologyEntity(_entityId: string): { entity: OntologyEntity | null; loading: boolean; error: Error | null } {
  return {
    entity: null,
    loading: false,
    error: null,
  };
}

// Entity service mock
export const entityService = {
  queryEntities: async (_params: OntologyQueryParams): Promise<OntologyEntity[]> => {
    return mockEntities;
  },
  getEntityById: async (entityId: string): Promise<OntologyEntity | null> => {
    return mockEntities.find(e => e.entity_id === entityId) || null;
  },
};
