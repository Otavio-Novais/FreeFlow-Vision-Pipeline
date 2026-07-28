-- Dados de exemplo para simulação do ambiente Free Flow
-- Ordem de inserção respeita as Foreign Keys

-- ==========================================
-- 1. CATEGORIAS DE PEDÁGIO (Tabela Base)
-- ==========================================
INSERT INTO toll_categories (name, description, base_price, vehicle_type) VALUES 
('Categoria 1', 'Carros de passeio, SUVs, picapes e utilitários', 5.50, 'carro'),
('Categoria 2', 'Motocicletas, motonetas e triciclos', 3.00, 'moto'),
('Categoria 3', 'Caminhões leves (2 eixos)', 11.00, 'caminhao_leve'),
('Categoria 4', 'Caminhões médios (3 eixos)', 16.50, 'caminhao_medio'),
('Categoria 5', 'Ônibus, caminhões pesados e tratores', 22.00, 'onibus');

-- ==========================================
-- 2. PÓRTICOS (Câmeras do Free Flow)
-- ==========================================
INSERT INTO toll_gates (gate_code, location, highway, direction) VALUES 
('PORT-ANH-01', 'Km 45 - Sentido Interior', 'Rodovia Anhanguera', 'norte'),
('PORT-ANH-02', 'Km 45 - Sentido Capital', 'Rodovia Anhanguera', 'sul'),
('PORT-BAN-01', 'Km 120 - Sentido Litoral', 'Rodovia Bandeirantes', 'leste');

-- ==========================================
-- 3. CONTAS (Clientes/Donos das Tags)
-- ==========================================
INSERT INTO accounts (owner_name, cpf_cnpj, email) VALUES 
('João da Silva', '123.456.789-00', 'joao.silva@email.com'),
('Maria Oliveira', '987.654.321-00', 'maria.oliveira@email.com'),
('Transportes Rápidos LTDA', '12.345.678/0001-90', 'frota@transportesrapidos.com.br');

-- ==========================================
-- 4. VEÍCULOS CADASTRADOS
-- ==========================================
INSERT INTO vehicles (plate, brand, model, year, category_id) VALUES 
('ABC1234', 'Honda', 'Civic', 2020, 1),       -- Carro do João
('IYJ7F53', 'Audi', 'A6', 2018, 1),          -- Carro da Maria (Placa do seu teste de OCR!)
('MOTO001', 'Yamaha', 'MT-07', 2021, 2),     -- Moto da Maria
('TRK1234', 'Volvo', 'FH 540', 2019, 4),     -- Caminhão da Empresa
('GHI5678', 'Fiat', 'Uno', 2015, 1);         -- Carro SEM tag (Para testar fluxo UNREGISTERED)

-- ==========================================
-- 5. TAGS OBO (Vínculo Tag -> Conta -> Veículo)
-- ==========================================
INSERT INTO obo_tags (tag_number, account_id, vehicle_id, is_active) VALUES 
('OBO-001', 1, 1, 1),  -- Tag do João (ABC1234)
('OBO-002', 2, 2, 1),  -- Tag da Maria (IYJ7F53)
('OBO-003', 2, 3, 1),  -- Tag da Maria (MOTO001)
('OBO-004', 3, 4, 1),  -- Tag da Empresa (TRK1234)
('OBO-005', 1, 1, 0);  -- Tag INATIVA do João (Para testar erro de tag inválida)

-- ==========================================
-- 6. TRANSAÇÕES HISTÓRICAS (Cenários de Teste)
-- ==========================================

-- Cenário 1: Passagem Normal (Tudo certo)
INSERT INTO transactions (timestamp, gate_id, plate_read, plate_confidence, vehicle_detected, vehicle_confidence, category_id, toll_amount, obo_tag_id, status, divergence_reason) VALUES 
(DATETIME('now', '-1 hour'), 1, 'IYJ7F53', 0.98, 'carro', 0.95, 1, 5.50, 2, 'PENDING', NULL);

-- Cenário 2: Divergência de Placa (OCR leu errado ou tentativa de fraude)
-- A tag OBO-002 passou, mas o OCR leu uma placa diferente da cadastrada (IYJ7F53)
INSERT INTO transactions (timestamp, gate_id, plate_read, plate_confidence, vehicle_detected, vehicle_confidence, category_id, toll_amount, obo_tag_id, status, divergence_reason) VALUES 
(DATETIME('now', '-30 minutes'), 1, 'XYZ9999', 0.85, 'carro', 0.90, 1, 5.50, 2, 'DIVERGENCE', 'Placa lida (XYZ9999) difere da placa cadastrada na tag (IYJ7F53)');

-- Cenário 3: Veículo sem Tag (UNREGISTERED)
-- O veículo GHI5678 passou, o OCR leu certo, mas não há tag OBO associada a ele.
INSERT INTO transactions (timestamp, gate_id, plate_read, plate_confidence, vehicle_detected, vehicle_confidence, category_id, toll_amount, obo_tag_id, status, divergence_reason) VALUES 
(DATETIME('now', '-15 minutes'), 2, 'GHI5678', 0.92, 'carro', 0.88, 1, 5.50, NULL, 'UNREGISTERED', 'Veículo identificado visualmente, mas sem tag OBO vinculada. Cobrança via boleto/notificação.');

-- Cenário 4: Divergência de Categoria (Tentativa de pagar menos)
-- Passou um Caminhão (TRK1234), mas a tag OBO-001 (que é de um Carro) foi lida na pista.
INSERT INTO transactions (timestamp, gate_id, plate_read, plate_confidence, vehicle_detected, vehicle_confidence, category_id, toll_amount, obo_tag_id, status, divergence_reason) VALUES 
(DATETIME('now', '-5 minutes'), 3, 'TRK1234', 0.99, 'caminhao_medio', 0.97, 4, 16.50, 1, 'DIVERGENCE', 'Categoria visual (caminhao_medio - R$16,50) difere da categoria da tag OBO-001 (carro - R$5,50). Auditoria necessária.');